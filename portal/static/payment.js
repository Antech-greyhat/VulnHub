// Mfano demo payment helper (client-side).
// NOTE: these values are shipped to every visitor's browser. Anything secret
// here is readable by anyone who opens the page source - which is the whole
// lesson. All values are FAKE.
const MFANO_PAYMENTS = {
  publicKey: "FAKE_MPESA_PUBLIC_KEY_123",
  // Oops: a "secret" key committed into client-side code.
  secretKey: "MFANO{fr0nt3nd_k3y_0p3n3d_th3_t1ll}",
  endpoint: "/payments/pay",
};

function prefillPayment() {
  // Purely cosmetic: the real amount is trusted server-side (see Phase 4).
  console.debug("Mfano payments ready", MFANO_PAYMENTS.publicKey);
}
document.addEventListener("DOMContentLoaded", prefillPayment);
