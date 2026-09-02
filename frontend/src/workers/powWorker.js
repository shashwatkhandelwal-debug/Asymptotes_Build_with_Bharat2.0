function countLeadingZeroBits(bytes) {
  let count = 0;
  for (let i = 0; i < bytes.length; i++) {
    const byte = bytes[i];
    if (byte === 0) {
      count += 8;
    } else {
      count += (8 - (32 - Math.clz32(byte)));
      break;
    }
  }
  return count;
}

self.onmessage = async (e) => {
  const { challenge_id, salt, difficulty_bits, max_attempts = 2000000 } = e.data;

  if (!difficulty_bits || difficulty_bits === 0) {
    self.postMessage({
      success: true,
      nonce: "0",
      attempts: 1,
      elapsed_ms: 0.01
    });
    return;
  }

  const startTime = performance.now();
  const encoder = new TextEncoder();
  const prefix = `${challenge_id}:${salt}:`;

  let nonce = 0;
  const batchSize = 1000;

  try {
    while (nonce < max_attempts) {
      for (let i = 0; i < batchSize && nonce < max_attempts; i++, nonce++) {
        const candidateStr = prefix + nonce;
        const candidateBytes = encoder.encode(candidateStr);
        const digestBuffer = await crypto.subtle.digest('SHA-256', candidateBytes);
        const digestBytes = new Uint8Array(digestBuffer);

        if (countLeadingZeroBits(digestBytes) >= difficulty_bits) {
          const elapsed = performance.now() - startTime;
          self.postMessage({
            success: true,
            nonce: nonce.toString(),
            attempts: nonce + 1,
            elapsed_ms: Math.round(elapsed * 100) / 100
          });
          return;
        }
      }
    }

    const elapsed = performance.now() - startTime;
    self.postMessage({
      success: false,
      nonce: null,
      attempts: max_attempts,
      elapsed_ms: Math.round(elapsed * 100) / 100,
      error: "Max attempts reached"
    });
  } catch (err) {
    self.postMessage({
      success: false,
      error: err.message
    });
  }
};
