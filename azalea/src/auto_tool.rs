use azalea_block::{BlockState, BlockTrait, fluid_state::FluidKind};
use azalea_client::{Client, inventory::Inventory};
use azalea_core::position::BlockPos;
use azalea_entity::{FluidOnEyes, Physics};
use azalea_inventory::{ItemStack, Menu, components};

use crate::BotClientExt;

#[derive(Debug)]
pub struct BestToolResult {
    pub index: usize,
    pub percentage_per_tick: f32,
}

pub trait AutoToolClientExt {
    fn best_tool_in_hotbar_for_block(&self, block: BlockState) -> BestToolResult;
    fn mine_with_auto_tool(&self, block_pos: BlockPos) -> impl Future<Output = ()> + Send;
}

impl AutoToolClientExt for Client {
    fn best_tool_in_hotbar_for_block(&self, block: BlockState) -> BestToolResult {
        let mut ecs = self.ecs.lock();
        let (inventory, physics, fluid_on_eyes) =
            self.query::<(&Inventory, &Physics, &FluidOnEyes)>(&mut ecs);
        let menu = &inventory.inventory_menu;

        accurate_best_tool_in_hotbar_for_block(block, menu, physics, fluid_on_eyes)
    }

    async fn mine_with_auto_tool(&self, block_pos: BlockPos) {
        let block_state = self
            .world()
            .read()
            .get_block_state(block_pos)
            .unwrap_or_default();
        let best_tool_result = self.best_tool_in_hotbar_for_block(block_state);
        self.set_selected_hotbar_slot(best_tool_result.index as u8);
        self.mine(block_pos).await;
    }
}

/// Returns the best tool in the hotbar for the given block.
///
/// Note that this doesn't take into account whether the player is on the ground
/// or in water, use [`accurate_best_tool_in_hotbar_for_block`] instead if you
/// care about those things.
pub fn best_tool_in_hotbar_for_block(block: BlockState, menu: &Menu) -> BestToolResult {
    let mut physics = Physics::default();
    physics.set_on_ground(true);

    accurate_best_tool_in_hotbar_for_block(
        block,
        menu,
        &physics,
        &FluidOnEyes::new(FluidKind::Empty),
    )
}

pub fn accurate_best_tool_in_hotbar_for_block(
    block: BlockState,
    menu: &Menu,
    physics: &Physics,
    fluid_on_eyes: &FluidOnEyes,
) -> BestToolResult {
    let hotbar_slots = &menu.slots()[menu.hotbar_slots_range()];

    let mut best_speed = 0.;
    let mut best_slot = None;

    let block = Box::<dyn BlockTrait>::from(block);
    let registry_block = block.as_registry_block();

    if matches!(
        registry_block,
        azalea_registry::Block::Water | azalea_registry::Block::Lava
    ) {
        // can't mine fluids
        return BestToolResult {
            index: 0,
            percentage_per_tick: 0.,
        };
    }

    // find the first slot that has an item without durability
    for (i, item_slot) in hotbar_slots.iter().enumerate() {
        let this_item_speed;
        match item_slot {
            ItemStack::Empty => {
                this_item_speed = Some(azalea_entity::mining::get_mine_progress(
                    block.as_ref(),
                    azalea_registry::Item::Air,
                    menu,
                    fluid_on_eyes,
                    physics,
                ));
            }
            ItemStack::Present(item_stack) => {
                // lazy way to avoid checking durability since azalea doesn't have durability
                // data yet
                if !item_stack.components.has::<components::Damage>() {
                    this_item_speed = Some(azalea_entity::mining::get_mine_progress(
                        block.as_ref(),
                        item_stack.kind,
                        menu,
                        fluid_on_eyes,
                        physics,
                    ));
                } else {
                    this_item_speed = None;
                }
            }
        }
        if let Some(this_item_speed) = this_item_speed
            && this_item_speed > best_speed
        {
            best_slot = Some(i);
            best_speed = this_item_speed;
        }
    }

    // now check every item
    for (i, item_slot) in hotbar_slots.iter().enumerate() {
        if let ItemStack::Present(item_slot) = item_slot {
            let this_item_speed = azalea_entity::mining::get_mine_progress(
                block.as_ref(),
                item_slot.kind,
                menu,
                fluid_on_eyes,
                physics,
            );
            if this_item_speed > best_speed {
                best_slot = Some(i);
                best_speed = this_item_speed;
            }
        }
    }

    BestToolResult {
        index: best_slot.unwrap_or(0),
        percentage_per_tick: best_speed,
    }
}
