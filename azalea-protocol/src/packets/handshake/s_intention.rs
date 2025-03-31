use std::hash::Hash;

use azalea_buf::AzBuf;
use azalea_protocol_macros::ServerboundHandshakePacket;

use crate::packets::ClientIntention;

#[derive(Hash, Clone, Debug, AzBuf, ServerboundHandshakePacket)]
pub struct ServerboundIntention {
    #[var]
    pub pver: i32,
    pub host: String,
    pub port: u16,
    pub next: ClientIntention,
}
