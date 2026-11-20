const form = document.getElementById("challenge-login");
form.addEventListener("submit", () => {
  const displayed = form.elements.namedItem("Username");
  const transmitted = document.createElement("input");
  transmitted.type = "hidden";
  transmitted.name = "username";
  transmitted.value = displayed.value;
  displayed.disabled = true;
  form.append(transmitted);
});
