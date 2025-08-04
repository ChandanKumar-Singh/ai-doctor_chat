def format_markdown_from_json(json_str: str) -> str:
    import json

    try:
        data = json.loads(json_str)
        r = data.get("response", {})
    except Exception:
        return f"```\n{json_str}\n```"  # fallback: raw view if not valid JSON

    def section(title: str, content: str) -> str:
        return f"\n---\n\n### {title}\n\n{content.strip() if content.strip() else '_None_'}\n"

    def bullet_list(items: list) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "_None_"

    def named_list(items: list) -> str:
        return "\n".join(f"- **{i.get('name', 'N/A')}**: {i.get('description', '')}" for i in items) if items else "_None_"

    def urgent_flags(items: list) -> str:
        return "\n".join(f"- **{i.get('condition', '')}**: {i.get('explanation', '')}" for i in items) if items else "_None_"

    summary = f"""## 📝 Summary\n\n{r.get("summary", "_No summary provided._")}\n\n**Confidence Level:** `{r.get("confidence_level", "unknown").upper()}`"""

    conditions = section("🧠 Possible Conditions", named_list(r.get("possible_conditions", [])))

    care = "\n".join([
        section("🧘 Self-care", bullet_list(r.get("recommended_care", {}).get("self-care", []))),
        section("💊 Medications", named_list(r.get("recommended_care", {}).get("medications", []))),
        section("🏃 Lifestyle", bullet_list(r.get("recommended_care", {}).get("lifestyle", [])))
    ])

    flags = section("🚨 Urgent Flags", urgent_flags(r.get("urgent_flags", [])))

    disclaimer = f"\n> ⚠️ {r.get("disclaimer", "This is not a diagnosis. Consult a real doctor.")}\n"

    return f"{summary}{conditions}{care}{flags}{disclaimer}"

