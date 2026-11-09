// Mfano "secure export" helper (client-side).
// NOTE: everything in this file is shipped to every visitor's browser.
//
// Phase 5b hardcoded-key lesson: the encrypted transcript below is AES-128-CBC,
// and the key needed to decrypt it is sitting right here next to it. A key that
// travels with the ciphertext is not a secret - the browser (and you) can
// decrypt it offline. The plaintext is a MFANO{...} flag. All values are FAKE.
const MFANO_SECURE_EXPORT = {
  cipher: "AES-128-CBC",
  // Hardcoded symmetric key (hex). This should have lived in a server-side vault.
  keyHex: "0f1e2d3c4b5a69788796a5b4c3d2e1f0",
  // base64( IV(16 bytes) || ciphertext ). Decrypt with the key above.
  encryptedTranscript:
    "ABEiM0RVZneImaq7zN3u/zZq3RYslyRepYavVAOlBbh+iLPcq610DptUyeh4UcXZ0dq4EnXt/FMxcSVth4sh9g==",
};

// Decrypt in Node:  node -e '...crypto.createDecipheriv("aes-128-cbc", key, iv)...'
// or in CyberChef:  From Base64 -> AES Decrypt (CBC, key hex, IV = first block).
console.debug("Mfano secure export ready", MFANO_SECURE_EXPORT.cipher);
