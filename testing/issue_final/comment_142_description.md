One more detail that makes this confusing for users: the help text next to the vehicle list in Additional Inputs > Loading says

> "Only checked vehicles are included in the analysis."

(`ui_fields_additional_input.py`, in the "Live Load (LL)" description block). As shown above, that is not what happens at the moment, so a user who unticks Class 70R reasonably assumes it was removed from the design. Either the selection should be wired into the analysis, or this text should be changed until it is.
