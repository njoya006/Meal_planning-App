const togglePassword = document.getElementById('togglePassword');
const password = document.getElementById('password');
const passwordError = document.getElementById('password-error');
const continueBtn = document.getElementById('continue-btn');

// Show/hide password
togglePassword.addEventListener('click', () => {
  const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
  password.setAttribute('type', type);
  togglePassword.textContent = type === 'password' ? '👁' : '🙈';
});

// Check password strength
password.addEventListener('input', () => {
  const val = password.value;
  const errors = [];

  if (val.length < 8) errors.push("• At least 8 characters");
  if (!/[a-z]/.test(val)) errors.push("• One lowercase letter");
  if (!/[A-Z]/.test(val)) errors.push("• One uppercase letter");
  if (!/[0-9]/.test(val)) errors.push("• One digit");
  if (!/[!@#\$%\^\&*\)\(+=._-]/.test(val)) errors.push("• One special character");
  if (/\s/.test(val)) errors.push("• No spaces allowed");
  if (["password", "12345678", "admin", "password123"].includes(val.toLowerCase())) errors.push("• Password too common");

  if (errors.length > 0) {
    passwordError.innerHTML = errors.join("<br>");
    passwordError.style.color = "red";
    continueBtn.disabled = true;
  } else {
    passwordError.innerHTML = "";
    continueBtn.disabled = false;
  }
});