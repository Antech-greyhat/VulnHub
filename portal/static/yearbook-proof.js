const prefix = "yearbook_preview=";
const cookie = document.cookie.split(/;\s*/).find(pair => pair.startsWith(prefix));
let preview;
try {
  preview = JSON.parse(atob(cookie?.slice(prefix.length) || ""));
} catch {
  // Keep the guest edition on screen if a cookie edit is incomplete.
}

if (preview?.user === "admin" && preview.role === "admin") {
  const edition = new TextEncoder().encode(`${preview.user}/${preview.role}`);
  const serial = Array.from(edition, byte => byte.toString(16).padStart(2, "0")).join("");
  const receipt = `MFANO{pr1nt_${serial}}`;
  document.getElementById("proof-edition").textContent = `Admin preview · Printer receipt ${receipt}`;
}
