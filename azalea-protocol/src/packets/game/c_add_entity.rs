use azalea_buf::AzBuf;
use azalea_core::{delta::PositionDelta8, position::Vec3, resource_location::ResourceLocation};
use azalea_entity::{metadata::apply_default_metadata, EntityBundle};
use azalea_protocol_macros::ClientboundGamePacket;
use azalea_world::MinecraftEntityId;
use uuid::Uuid;

#[derive(Clone, Debug, AzBuf, ClientboundGamePacket)]
pub struct ClientboundAddEntity {
    /// The numeric ID of the entity being added to the world.
    #[var]
    pub id: MinecraftEntityId,
    pub uuid: Uuid,
    pub entity_type: azalea_registry::EntityKind,
    pub position: Vec3,
    pub x_rot: i8,
    pub y_rot: i8,
    pub y_head_rot: i8,
    #[var]
    pub data: i32,
    pub velocity: PositionDelta8,
}

impl ClientboundAddEntity {
    /// Make the entity into a bundle that can be inserted into the ECS. You
    /// must apply the metadata after inserting the bundle with
    /// [`Self::apply_metadata`].
    pub fn as_entity_bundle(&self, world_name: ResourceLocation) -> EntityBundle {
        EntityBundle::new(self.uuid, self.position, self.entity_type, world_name)
    }

    /// Apply the default metadata for the given entity.
    pub fn apply_metadata(&self, entity: &mut bevy_ecs::system::EntityCommands) {
        apply_default_metadata(entity, self.entity_type);
    }
}
