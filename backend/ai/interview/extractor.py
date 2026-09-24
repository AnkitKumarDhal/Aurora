                None,
                False,
            )

        if target == "bowel_changes":
            if any(
                term in normalized
                for term in (
                    "constipation",
                    "constipated",
                    "कब्ज",
                )
            ):
                return (
                    "constipation",
                    False,
                )

            if any(
                term in normalized
                for term in (
                    "diarrhea",
                    "loose stools",
                    "loose motions",
                    "दस्त",
                )
            ):
                return (
                    "diarrhea",
                    False,
                )

            return (
                None,
                False,
            )

        if target == "aggravating_factors":
            patterns = (
                r"\b(?:makes|make|made|makes it)\s+worse\b",
                r"\bworse when\b([^,.!?;]+)",
                r"\bworse with\b([^,.!?;]+)",
                r"\bgets worse when\b([^,.!?;]+)",
                r"\bgets worse with\b([^,.!?;]+)",
            )

            for pattern in patterns:
                match = re.search(
                    pattern,
                    normalized,
                )

                if match:
                    value = (
                        match.group(1).strip()
                        if match.lastindex
                        else "reported"
                    )

                    return (
                        value,
                        False,
                    )

            return (
                None,
                False,
            )

        if target == "relieving_factors":
            patterns = (
                r"\b(?:makes|make|made|makes it)\s+better\b",
                r"\bbetter when\b([^,.!?;]+)",
                r"\bbetter with\b([^,.!?;]+)",
                r"\bgets better when\b([^,.!?;]+)",
                r"\bgets better with\b([^,.!?;]+)",
                r"\bhelps\b([^,.!?;]*)",
            )

            for pattern in patterns:
                match = re.search(
                    pattern,
                    normalized,
                )

                if match:
                    value = (
                        match.group(1).strip()
                        if match.lastindex
                        else "reported"
                    )

                    return (
                        value,
                        False,
                    )

            return (
                None,
                False,
            )

        if target == "occupation":
            patterns = (
                r"\b(?:desk job|office job|works? as|work as|job is|occupation is)\s*([^,.!?;]*)",
                r"(?:मैं|मेरी)\s+(?:एक\s+)?(छात्र|विद्यार्थी|शिक्षक|इंजीनियर|डॉक्टर|किसान|व्यवसायी|नौकरी|व्यापारी)",
                r"\b(i am|i'm)\s+(?:a\s+)?(student|teacher|engineer|doctor|farmer|businessman|businesswoman)\b",
            )

            for pattern in patterns:
                match = re.search(
                    pattern,
                    normalized,
                )
                if match:
                    return (
                        match.group(0).strip(),
                        False,
                    )

            return (
                None,
                False,
            )

        if target == "diet":
            match = re.search(
                r"\b(?:i eat|my diet is|my usual diet is|diet consists of)\s+"
                r"([^,.!?;]+)",
                normalized,
            )

            if match:
                return (
                    match.group(1).strip(),
                    False,
                )

            if any(
                term in normalized
                for term in (
                    "roti",
                    "rice",
                    "potato",
                    "vegetable",
                    "meals",
                    "vegetarian",
                    "veg",
                    "non-veg",
                    "non veg",
                    "शाकाहारी",
                    "मांसाहारी",
                    "शाकाहार",
                    "मांसाहार",
                    "घर का खाना",
                    "दूध",
                    "चावल",
                    "रोटी",
                    "सब्जी",
                    "सब्ज़ी",
                )
            ):
                return (
                    text.strip(),
                    False,
                )

            return (
                None,
                False,
            )

        if target == "sleep":
            if re.search(
                r"\b(?:very good|good|poor|bad|normal|disturbed)\s+sleep\b",
                normalized,
            ) or re.search(
                r"\b\d+(?:\.\d+)?\s*(?:hours?|hrs?)\s+(?:of\s+)?sleep\b",
                normalized,
            ) or re.search(
                r"\b\d+(?:\.\d+)?\s*घंटे\b.*(?:नींद|सोता|सोती|सोना)",
                normalized,
            ) or any(
                term in normalized
                for term in (
                    "अच्छी नींद",
                    "कम नींद",
                    "नींद खराब",
                    "नींद ठीक",
                    "नींद नहीं आती",
                    "sleep",
                )
            ):
                return (
                    text.strip(),
                    False,
                )

            return (
                None,
                False,
            )

        if target == "physical_activity":
            if any(
                term in normalized
                for term in (
                    "not much",
                    "very little",
                    "little exercise",
                    "no exercise",
                    "physical activity",
                    "exercise",
                    "walking",
                    "gym",
                    "active",
                    "व्यायाम",
                    "चलना",
                    "टहलना",
                    "कसरत",
                    "सक्रिय",
                    "exercise nahi",
                    "vyayam",
                    "walking karta",
                    "walk karta",
                    "walk karti",
                )
            ):
                return (
                    text.strip(),
                    False,
                )

            return (
                None,
                False,
            )

        if target in TEXT_TARGET_TERMS:
            terms = TEXT_TARGET_TERMS[
                target
            ]

            if any(
                term in normalized
                for term in terms
            ):
                negative = False
