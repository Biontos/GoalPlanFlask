document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("dark-mode-toggle");

    function applyDarkMode(state) {
        if (state === "enabled") {
            document.body.classList.add("dark-mode");
            document.documentElement.style.setProperty("--background-color", "#121212");
            document.documentElement.style.setProperty("--text-color", "#ffffff");
            toggleButton.textContent = "Светлая тема";
        } else {
            document.body.classList.remove("dark-mode");
            document.documentElement.style.setProperty("--background-color", "#ffffff");
            document.documentElement.style.setProperty("--text-color", "#000000");
            toggleButton.textContent = "Темная тема";
        }
    }

    const darkMode = localStorage.getItem("dark-mode") || "disabled";
    applyDarkMode(darkMode);

    toggleButton.addEventListener("click", function () {
        const newMode = document.body.classList.contains("dark-mode") ? "disabled" : "enabled";
        localStorage.setItem("dark-mode", newMode);
        applyDarkMode(newMode);
    });
});
