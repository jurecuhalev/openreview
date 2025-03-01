def merge_fields_with_submission_data(fields: list, data: dict, excluded_labels=[], include_empty=False) -> list:
    results = []
    for field in fields:
        field_id = field.get("id")
        description = field.get("description", "")
        if field.get("inputs"):
            input_fields = []
            for input_field in field.get("inputs"):
                input_id = str(input_field.get("id"))
                input_field_id = input_field.get("id")
                label = input_field.get("label")
                label_with_id = f"{label} [{input_field_id}]"
                value = data.get(input_id, "")
                _type = input_field.get("type")
                if not _type:
                    _type = field.get("type")

                if value or include_empty:
                    input_fields.append(
                        {
                            "label": label,
                            "label_with_id": label_with_id,
                            "value": value,
                            "type": _type,
                        }
                    )

            label = field.get("label")
            label_with_id = f"{label} [{field_id}]"
            _type = field.get("type")

            if label not in excluded_labels:
                results.append(
                    {
                        "label": label,
                        "label_with_id": label_with_id,
                        "type": _type,
                        "inputs": input_fields,
                        "description": description,
                    }
                )

        elif field.get("type") == "list":
            label = field.get("label")
            label_with_id = f"{label} [{field_id}]"

            results.append(
                {
                    "label": label,
                    "label_with_id": label_with_id,
                    "type": "text",
                    "description": description,
                }
            )
            for list_data in data.get(str(field.get("id"))):
                input_fields = []

                id_counter = 0
                for input_field in field.get("choices"):
                    id_counter += 1
                    input_id = str(input_field.get("text"))
                    input_field_id = id_counter
                    label = input_field.get("text")
                    label_with_id = f"{label} [{input_field_id}]"
                    value = list_data.get(input_id, "")

                    _type = input_field.get("type")
                    if not _type:
                        _type = field.get("type")

                    if value or include_empty:
                        input_fields.append(
                            {
                                "label": label,
                                "label_with_id": label_with_id,
                                "value": value,
                                "type": _type,
                            }
                        )

                    label = field.get("label")
                    _type = field.get("type")

                if label not in excluded_labels:
                    results.append(
                        {
                            "label": "",
                            "type": _type,
                            "inputs": input_fields,
                            "description": description,
                        }
                    )
        else:
            label = field.get("label")
            field_id = str(field.get("id"))
            label_with_id = f"{label} [{field_id}]"
            value = data.get(field_id, "")
            _type = field.get("type")

            if label not in excluded_labels:
                if _type == "section" or value:
                    results.append(
                        {
                            "label": label,
                            "label_with_id": label_with_id,
                            "value": value,
                            "type": _type,
                            "description": description,
                        }
                    )

    return results


def extract_search_text(entry) -> str:
    entry_data = merge_fields_with_submission_data(fields=entry.project.fields, data=entry.data, include_empty=True)

    text = []
    for row in entry_data:
        if row.get("inputs"):
            for input_row in row.get("inputs"):
                text.append(input_row["value"])
        elif value := row.get("value"):
            text.append(value)

    text = [t for t in text if t]

    return "\n".join(text)
