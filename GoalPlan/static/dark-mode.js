<script>
    document.addEventListener("DOMContentLoaded", function () {
        const toggleButton = document.getElementById("dark-mode-toggle");

        if (typeof(Storage) !== "undefined") {
            const isDarkMode = localStorage.getItem("dark-mode") === "enabled";

            if (isDarkMode) {
                document.body.classList.add("dark-mode");
                document.documentElement.style.setProperty("--background-color", "#121212");
                document.documentElement.style.setProperty("--text-color", "#ffffff");
                toggleButton.textContent = "Светлая тема";
            }

            toggleButton.addEventListener("click", function () {
                document.body.classList.toggle("dark-mode");

                if (document.body.classList.contains("dark-mode")) {
                    localStorage.setItem("dark-mode", "enabled");
                    document.documentElement.style.setProperty("--background-color", "#121212");
                    document.documentElement.style.setProperty("--text-color", "#ffffff");
                    toggleButton.textContent = "Светлая тема";
                } else {
                    localStorage.setItem("dark-mode", "disabled");
                    document.documentElement.style.setProperty("--background-color", "#ffffff");
                    document.documentElement.style.setProperty("--text-color", "#000000");
                    toggleButton.textContent = "Темная тема";
                }
            });
        } else {
            console.error("localStorage не поддерживается в этом браузере.");
        }
    });
</script>
