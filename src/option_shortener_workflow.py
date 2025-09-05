from typing import Dict
from general import extract_mcq_components, extract_correct_answer_letter
from option_shortening_helper import identify_longer_options, syntactic_analysis, calculate_length_range


def check_and_shorten_long_option(mcq:str)->Dict:
    # step 1: find the options 
    question, options = extract_mcq_components(mcq)
    correct_answer_letter = extract_correct_answer_letter(mcq)

    # step2: check if any option is noticeably longer than the others
    longer_option_indices = identify_longer_options(options)
    if not longer_option_indices:
        return {}  # No option needs shortening

    # step3: if so, first analyze the syntactic structure of the options 
    identified_rule = syntactic_analysis(model="gpt-4o",
                                            temperature=0.3,
                                            question_stem=question,
                                            options=options)
    # step4: calculate the target length for the shortening model to aim for (based on the lengths of the other options)
    min_length, max_length = calculate_length_range(options)

    # step5: shorten the longer option using the option shortener model to generate 5 candidates
    
    # step6: use the option ranker model to pick the best candidate, if none is good enough, keep the original option.
    pass