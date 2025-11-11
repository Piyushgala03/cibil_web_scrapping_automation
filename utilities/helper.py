import re
import pandas as pd

# Sample test inputs — add more here to see behavior
sample_names = [
    "Mr. Ramesh S/O Dinesh Kumar",
    "Ms. Ramesh S/O Dinesh Kumar",
    "Ms Ramesh S/O Dinesh Kumar",
    "Mr Ramesh S/O Dinesh Kumar",
    "Mrs Ramesh S/O Dinesh Kumar",
    "Mrs. Ramesh S/O Dinesh Kumar",
    "M/s ABC Pvt Ltd",
    "M/s. ABC Pvt Ltd",
    "M/s. ABC (P) Ltd",
    "ABC (P)",
    "ABC (prop)",
    "Dr. Seema Sharma (Director)",
    "Dr Seema Sharma (Director)",
    "Sh Rakesh (Executive Director)",
    "ch Rakesh (Executive Director)",
    "ch Rakesh (Ex Director)",
    "ch Rakesh Director EX",
    "ch Rakesh Director (EX)",
    "Co-applicant Anil",
    "Whole Time Director Priya",
    "Proprietor Rajesh Kumar",
    "ABC Corp in liquidation",
    "Sharma (IND)",
    "Miss Neeta (P) Ltd",
    "Ch. Mehta",
    "Smt Rekha Devi Partner",
    "Smti Rekha Devi Partner",
    "Smti Rekha Devi corp",
    "Smti Rekha Devi proprietor",
    "Smti Rekha Devi (proprietor)",
    "Smti Rekha Devi proprieter",
    "Smti Rekha Devi (proprieter)",
    "Smti Rekha Devi ERSTWHILE PROMOTER",
    "HEM SINGH BHARANA (PROMOTER DIRECTOR/ GUARANTOR)",
    "HEM SINGH BHARANA GUARANTOR of ",
]

# Convert to DataFrame
df = pd.DataFrame({"Final_DirectorName": sample_names})

df["Cleaned_Name"] = (
    df["Final_DirectorName"].astype(str)
    .str.lower()
    .str.strip()

    # Remove dots
    .str.replace(r'\.', ' ', regex=True)

    # Remove honorifics
    .replace(r'\bm/s\b', '', regex=True)
    .replace(r'\bmr\b', '', regex=True)
    .replace(r'\bmrs\b', '', regex=True)
    .replace(r'\bms\b', '', regex=True)
    .replace(r'\bdr\b', '', regex=True)

    # Company type replacements
    .replace(r'\(?p\)?\s*ltd\b', 'private limited', regex=True)
    .replace(r'\(p\)\s*', 'private', regex=True)
    .replace(r'\bpvtltd\b', 'private limited', regex=True)
    .replace(r'\bpvt\b', 'private', regex=True)
    .replace(r'\bltd\b', 'limited', regex=True)
    .replace(r'\bsoc\b', 'society', regex=True)
    .replace(r'\bcorp\b', 'corporation', regex=True)

    # Unwanted words / suffixes
    .replace(r'\bsmt\b', '', regex=True)
    .replace(r'\bsmti\b', '', regex=True)
    .replace(r'\bmiss\b', '', regex=True)
    .replace(r'\bindividual\b', '', regex=True)
    .replace(r'\bchairman\b', '', regex=True)
    .replace(r'\bmanaging director\b', '', regex=True)
    .replace(r'\berstwhile\s+promoter\b', '', regex=True)
    .replace(r'^\s*guarantors?\s+of\s+', '', regex=True)        # e.g., "Guarantors of Rajesh Kumar"
    .replace(r'\bguarantors?\s+of\b', '', regex=True)
    .replace(r'\(.*promoter.*guarantor.*\)', '', regex=True)    # e.g., (PROMOTER DIRECTOR/ GUARANTOR)
    .replace(r'\(.*guarantor.*promoter.*\)', '', regex=True)


    .replace(r'\bpartner\b', '', regex=True)
    .replace(r'\(?\b(b)?prop(riet([oe]r)?)?\)?', '', regex=True)   # handles (prop), bprop, proprietor, etc.
    .replace(r'\(?ind\)?\s*', '', regex=True)
    .replace(r'\bin liquidation\b', '', regex=True)

    # Remove titles before name (start only)
    .replace(r'^\s*co[-\s]*applicant\s*', '', regex=True)
    .replace(r'^\s*\(?whole\s*time\s*director\)?\s*', '', regex=True)
    .replace(r'^\s*directors?\s*/\s*corporate\s*', '', regex=True)
    .replace(r'^\s*(sh|ch)\.?\s+', '', regex=True)
    .replace(r'^\s*\(\s*\)\s*', '', regex=True)

    # Remove director variants at END
    .replace(r'\s*\(?ex(?:ecutive)?\s*director[s]?\)?\s*$', '', regex=True)
    .replace(r'\s*\(?director\s*(?:ex|\(ex\))?\)?\s*$', '', regex=True)  # handles Director EX or (EX)

    # Remove parent info
    .replace(r'\(?\s*(s|d|w)/o[^,;]*', '', regex=True)

    # Remove leftover empty parentheses
    .replace(r'\(\s*\)', '', regex=True)

    # Normalize spaces and format
    .replace(r'\s+', ' ', regex=True)
    .str.upper()
    .str.strip()
)

print(df[['Final_DirectorName', 'Cleaned_Name']].to_string(index=False))