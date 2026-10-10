async def _generate_programming_explanation(prompt: str, language: str, formula: str, context: str) -> Optional[ProgrammingExplanation]:
    """
    Generate a programming concept explanation using the programming solution service.
    """
    try:
        # Use the programming solution service to get step-by-step explanation
        steps_data = programming_solution_service.explain_concept(prompt, language)

        if not steps_data:
            return None

        # Convert to ProgrammingStep objects
        steps = []
        for step_data in steps_data:
            step_obj = ProgrammingStep(
                step_number=step_data["step_number"],
                explanation=step_data["explanation"],
                code_example=CodeExample(
                    language=step_data["code_example"]["language"] if step_data["code_example"] else language,
                    code=step_data["code_example"]["code"] if step_data["code_example"] else "",
                    explanation=step_data["code_example"]["explanation"] if step_data["code_example"] else ""
                ) if step_data["code_example"] else None
            )
            steps.append(step_obj)

        # Create the programming explanation
        return ProgrammingExplanation(
            concept=prompt[:100],  # Truncate long prompts
            language=language,
            steps=steps,
            related_concepts=[f"{language} basics", f"{language} best practices"],
            complexity_analysis={"time": "O(1)", "space": "O(1)"} if language == "python" else None
        )
    except Exception as e:
        logger.warning(f"Failed to generate programming explanation via service: {e}")
        return None