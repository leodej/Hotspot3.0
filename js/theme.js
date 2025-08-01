// Função para alternar entre temas claro e escuro
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme") || "light"
  const newTheme = currentTheme === "light" ? "dark" : "light"

  // Atualizar o atributo data-theme no elemento HTML
  document.documentElement.setAttribute("data-theme", newTheme)

  // Salvar a preferência do usuário no localStorage
  localStorage.setItem("theme", newTheme)

  // Atualizar o ícone do botão
  updateThemeIcon(newTheme)
}

// Função para atualizar o ícone do botão de tema
function updateThemeIcon(theme) {
  const themeIcon = document.getElementById("theme-icon")
  if (themeIcon) {
    if (theme === "dark") {
      themeIcon.classList.remove("bi-moon")
      themeIcon.classList.add("bi-sun")
    } else {
      themeIcon.classList.remove("bi-sun")
      themeIcon.classList.add("bi-moon")
    }
  }
}

// Função para aplicar o tema salvo ou o tema do sistema
function applyTheme() {
  // Verificar se há uma preferência salva
  let theme = localStorage.getItem("theme")

  // Se não houver preferência salva, verificar a preferência do sistema
  if (!theme) {
    // Verificar se o usuário prefere o tema escuro no sistema
    const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)").matches
    theme = prefersDarkScheme ? "dark" : "light"
  }

  // Aplicar o tema
  document.documentElement.setAttribute("data-theme", theme)

  // Atualizar o ícone do botão
  updateThemeIcon(theme)
}

// Aplicar o tema quando o DOM estiver carregado
document.addEventListener("DOMContentLoaded", () => {
  applyTheme()

  // Adicionar evento de clique ao botão de tema
  const themeToggle = document.getElementById("theme-toggle")
  if (themeToggle) {
    themeToggle.addEventListener("click", toggleTheme)
  }
})
