let workerInstance = null;

function getWorker() {
  if (!workerInstance && typeof window !== 'undefined') {
    workerInstance = new Worker(new URL('../workers/powWorker.js', import.meta.url), {
      type: 'module'
    });
  }
  return workerInstance;
}

export function solvePoWChallenge(challenge) {
  return new Promise((resolve, reject) => {
    try {
      const worker = getWorker();
      const handler = (e) => {
        worker.removeEventListener('message', handler);
        if (e.data.success) {
          resolve(e.data);
        } else {
          reject(new Error(e.data.error || 'Failed to solve PoW'));
        }
      };

      worker.addEventListener('message', handler);
      worker.postMessage({
        challenge_id: challenge.challenge_id,
        salt: challenge.salt,
        difficulty_bits: challenge.difficulty_bits,
        max_attempts: 2000000
      });
    } catch (err) {
      reject(err);
    }
  });
}

export async function fetchWithAdaptivePoW(url, options = {}) {
  const initialResponse = await fetch(url, options);

  if (initialResponse.status === 428) {
    const errorData = await initialResponse.json();
    const challenge = errorData.challenge;

    if (!challenge) {
      throw new Error("Received 428 but no challenge payload provided.");
    }

    const solveResult = await solvePoWChallenge(challenge);

    const retryHeaders = {
      ...(options.headers || {}),
      'X-PoW-Nonce': solveResult.nonce,
      'X-PoW-Challenge-ID': challenge.challenge_id,
      'X-PoW-Timestamp': challenge.timestamp.toString(),
      'X-PoW-Difficulty': challenge.difficulty_bits.toString(),
      'X-PoW-Salt': challenge.salt,
      'X-PoW-Signature': challenge.signature
    };

    return await fetch(url, {
      ...options,
      headers: retryHeaders
    });
  }

  return initialResponse;
}
