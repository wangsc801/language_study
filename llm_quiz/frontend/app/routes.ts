import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  route("/", "layout.tsx", [
    index("routes/home.tsx"),
    route("settings", "routes/settings.tsx"),
    route("prompts", "routes/prompts.tsx"),
    route("prompts/new", "routes/prompts-new.tsx"),
    route("prompts/:language/:slug/edit", "routes/prompts-edit.tsx"),
    route("quizzes", "routes/quizzes.tsx"),
    route("languages", "routes/languages.tsx"),
    route("languages/new", "routes/languages-new.tsx"),
    route("languages/:code/edit", "routes/languages-edit.tsx"),
  ]),
] satisfies RouteConfig;