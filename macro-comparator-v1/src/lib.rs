//! Telegraph comparator module: the network's reference rule, per "Comparator modules" in
//! anjoman.ai/docs/scoring/build-a-scoring-module (Exact, AbsTol, RelTol, PassFail; linear falloff to 2x tolerance).
#![cfg_attr(target_arch = "wasm32", no_std)]

const ONE: i64 = 10_000;

/// Score in basis points. `code` is read at 32-bit width; unknown codes are Exact.
pub fn score(truth: i64, miner: i64, code: i64, tol: i64) -> i64 {
    let code = code as i32;
    if !(code == 1 || code == 2) {
        return if miner == truth { ONE } else { 0 };
    }
    let diff = (miner as i128 - truth as i128).abs(); // i128: no wrap on opposite-sign extremes
    let err = if code == 1 { diff } else { diff * ONE as i128 / (truth as i128).abs().max(1) };
    let err = err.min(i64::MAX as i128) as i64;
    if tol <= 0 {
        return if err == 0 { ONE } else { 0 }; // as the kit: RelTol error truncated to 0 bp counts as exact
    }
    let window = tol.saturating_mul(2);
    if err >= window {
        return 0;
    }
    ONE.saturating_mul(window - err) / window // saturating, as the kit's linear_decay
}

#[cfg(target_arch = "wasm32")]
mod abi {
    static mut SPEC: [u8; 64] = [0; 64];

    #[no_mangle]
    pub extern "C" fn imw_alloc(size: i32) -> i32 {
        if size < 0 || size > 64 { return 0; }
        core::ptr::addr_of_mut!(SPEC) as i32
    }

    #[no_mangle]
    pub extern "C" fn imw_free(_ptr: i32, _size: i32) {}

    #[no_mangle]
    pub extern "C" fn imw_score_deterministic(truth: i64, miner: i64, spec_ptr: i32) -> i64 {
        // The node writes 16 bytes at spec_ptr: little-endian i64 code, then i64 tolerance.
        let p = spec_ptr as usize as *const u8;
        let rd = |o: usize| unsafe { i64::from_le_bytes(core::ptr::read_unaligned(p.add(o) as *const [u8; 8])) };
        super::score(truth, miner, rd(0), rd(8))
    }

    #[panic_handler]
    fn panic(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }
}
