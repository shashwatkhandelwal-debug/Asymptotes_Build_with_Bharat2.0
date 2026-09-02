"""
Tamper-Evident Hash-Chained Audit Ledger.
Stores every issued PoW challenge, solved proof, and dropped request in an append-only,
cryptographically linked SQLite ledger.

HONESTY NOTICE:
This is a local hash-chained append-only audit log demonstrating cryptographic tamper-evidence.
It is not a distributed consensus blockchain (no peer-to-peer gossip or mining consensus).
"""
import sqlite3
import hashlib
import time
import os
import json
from typing import List, Dict, Any, Optional, Tuple

class AuditLedger:
    def __init__(self, db_path: str = "backend/ledger.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    block_index INTEGER NOT NULL UNIQUE,
                    timestamp REAL NOT NULL,
                    client_ip TEXT NOT NULL,
                    difficulty_bits INTEGER NOT NULL,
                    challenge_id TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    status TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    block_hash TEXT NOT NULL
                )
            """)
            conn.commit()

            # Insert Genesis block if empty
            cursor.execute("SELECT COUNT(*) as count FROM audit_ledger")
            count = cursor.fetchone()["count"]
            if count == 0:
                self._insert_genesis_block(conn)

    def _calculate_block_hash(
        self,
        block_index: int,
        timestamp: float,
        client_ip: str,
        difficulty_bits: int,
        challenge_id: str,
        nonce: str,
        status: str,
        prev_hash: str
    ) -> str:
        payload = f"{block_index}:{timestamp}:{client_ip}:{difficulty_bits}:{challenge_id}:{nonce}:{status}:{prev_hash}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _insert_genesis_block(self, conn):
        timestamp = 1772500000.0
        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        block_hash = self._calculate_block_hash(
            0, timestamp, "0.0.0.0", 0, "GENESIS_CHALLENGE", "0", "GENESIS", prev_hash
        )
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_ledger (
                block_index, timestamp, client_ip, difficulty_bits,
                challenge_id, nonce, status, prev_hash, block_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (0, timestamp, "0.0.0.0", 0, "GENESIS_CHALLENGE", "0", "GENESIS", prev_hash, block_hash))
        conn.commit()

    def get_latest_block(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_ledger ORDER BY block_index DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}

    def append_entry(
        self,
        client_ip: str,
        difficulty_bits: int,
        challenge_id: str,
        nonce: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Appends a new challenge event to the hash chain.
        Cryptographically links to the latest block hash.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT block_index, block_hash FROM audit_ledger ORDER BY block_index DESC LIMIT 1")
            latest = cursor.fetchone()

            new_index = (latest["block_index"] + 1) if latest else 0
            prev_hash = latest["block_hash"] if latest else "0" * 64
            timestamp = time.time()

            block_hash = self._calculate_block_hash(
                new_index, timestamp, client_ip, difficulty_bits, challenge_id, nonce, status, prev_hash
            )

            cursor.execute("""
                INSERT INTO audit_ledger (
                    block_index, timestamp, client_ip, difficulty_bits,
                    challenge_id, nonce, status, prev_hash, block_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_index, timestamp, client_ip, difficulty_bits, challenge_id, nonce, status, prev_hash, block_hash))
            conn.commit()

            return {
                "block_index": new_index,
                "timestamp": timestamp,
                "client_ip": client_ip,
                "difficulty_bits": difficulty_bits,
                "challenge_id": challenge_id,
                "nonce": nonce,
                "status": status,
                "prev_hash": prev_hash,
                "block_hash": block_hash
            }

    def verify_chain(self) -> Dict[str, Any]:
        """
        Walks the entire ledger sequentially from Genesis block to latest block.
        Verifies:
        1. Every block's internal hash matches recomputed hash of its contents.
        2. Every block's prev_hash matches the previous block's actual block_hash.
        Returns detailed verification report.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_ledger ORDER BY block_index ASC")
            blocks = [dict(row) for row in cursor.fetchall()]

            if not blocks:
                return {
                    "is_valid": False,
                    "total_blocks": 0,
                    "tampered_block_index": None,
                    "message": "Ledger is empty."
                }

            expected_prev_hash = "0" * 64

            for i, block in enumerate(blocks):
                # 1. Check previous hash linkage
                if i > 0 and block["prev_hash"] != expected_prev_hash:
                    return {
                        "is_valid": False,
                        "total_blocks": len(blocks),
                        "tampered_block_index": block["block_index"],
                        "error_type": "BROKEN_LINKAGE",
                        "message": f"Block #{block['block_index']} prev_hash does not match Block #{i-1} block_hash! Tampering detected in chain link.",
                        "expected_prev_hash": expected_prev_hash,
                        "actual_prev_hash": block["prev_hash"]
                    }

                # 2. Check internal block integrity
                recomputed_hash = self._calculate_block_hash(
                    block["block_index"],
                    block["timestamp"],
                    block["client_ip"],
                    block["difficulty_bits"],
                    block["challenge_id"],
                    block["nonce"],
                    block["status"],
                    block["prev_hash"]
                )

                if recomputed_hash != block["block_hash"]:
                    return {
                        "is_valid": False,
                        "total_blocks": len(blocks),
                        "tampered_block_index": block["block_index"],
                        "error_type": "ALTERED_PAYLOAD",
                        "message": f"Block #{block['block_index']} payload hash mismatch! Contents altered without updating cryptographic signature.",
                        "expected_hash": recomputed_hash,
                        "actual_stored_hash": block["block_hash"]
                    }

                expected_prev_hash = block["block_hash"]

            return {
                "is_valid": True,
                "total_blocks": len(blocks),
                "tampered_block_index": None,
                "error_type": None,
                "message": f"All {len(blocks)} blocks cryptographically verified. Hash chain integrity intact."
            }

    def tamper_block_for_demo(self, block_index: int, new_status: str = "TAMPERED_SOLVED") -> Dict[str, Any]:
        """
        Stage Demo Feature:
        Intentionally alters a row in SQLite without updating the hash chain
        to prove live tamper-detection on stage.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_ledger WHERE block_index = ?", (block_index,))
            target = cursor.fetchone()
            if not target:
                # If block_index doesn't exist, tamper the latest non-genesis block
                cursor.execute("SELECT * FROM audit_ledger ORDER BY block_index DESC LIMIT 1")
                target = cursor.fetchone()

            if not target:
                return {"success": False, "message": "No blocks available to tamper."}

            target_index = target["block_index"]
            cursor.execute(
                "UPDATE audit_ledger SET status = ? WHERE block_index = ?",
                (new_status, target_index)
            )
            conn.commit()

            return {
                "success": True,
                "tampered_block_index": target_index,
                "old_status": target["status"],
                "new_status": new_status,
                "message": f"Block #{target_index} modified in database. Chain verification will now catch this tamper."
            }

    def get_blocks(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audit_ledger ORDER BY block_index DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]

    def reset_demo_ledger(self):
        """
        Stage Demo Reset:
        Clears demo session logs and re-initializes Genesis block.
        Framed explicitly as local demo environment reset.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS audit_ledger")
            conn.commit()
        self._init_db()

ledger = AuditLedger()
