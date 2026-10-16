import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        environment: "jsdom",
        include: ["tests/js/**/*.test.js"],
        coverage: {
            provider: "v8",
            reporter: [["text", { skipFull: true }]],
            include: [
                "src/django_form_matrix/static/django_form_matrix/**/*.js",
            ],
        },
    },
});
