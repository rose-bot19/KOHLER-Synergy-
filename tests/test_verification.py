from verification import verify_grounding


evidence = """
Smart toilets are covered by a limited warranty.

The warranty period is 3 years from the original purchase date.

Warranty questions may require the model number and serial number.
"""


print("\n--- VALID RESPONSE ---")

answer = """
The smart toilet has a 3-year limited warranty.
The model number and serial number may be required
for warranty verification.
"""

print(
    verify_grounding(
        answer,
        evidence,
    )
)


print("\n--- SUSPICIOUS RESPONSE ---")

answer = """
The smart toilet is covered until March 2030.
"""

print(
    verify_grounding(
        answer,
        evidence,
    )
)