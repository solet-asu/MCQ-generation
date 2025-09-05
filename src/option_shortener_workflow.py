from typing import Dict, Tuple
from general import extract_mcq_components, extract_correct_answer_letter
from option_shortening_helper import identify_longer_options, syntactic_analysis, calculate_length_range, generate_candidate_short_options, select_best_candidate, update_mcq_with_new_option
import ast

def check_and_shorten_long_option(invocation_id:str, mcq:str, model:str="gpt-4o")->Tuple[str, Dict]:
    # step 1: find the options 
    question, options = extract_mcq_components(mcq)
    correct_answer_letter = extract_correct_answer_letter(mcq)

    # step2: check if any option is noticeably longer than the others
    longer_option_index, longer_option_text = identify_longer_options(options)
    if not longer_option_text:
        return (mcq, {})  # No option needs shortening

    input_tokens_accumulated = 0
    output_tokens_accumulated = 0
    # step3: if so, first analyze the syntactic structure of the options 
    identified_rule_meta = syntactic_analysis(
        invocation_id=invocation_id,
        model=model,
        temperature=0.3,
        question_stem=question,
        options=options)
    identified_rule = identified_rule_meta.get("syntactic_rule", "")
    input_tokens_accumulated += int(identified_rule_meta.get("input_tokens") or 0)
    output_tokens_accumulated += int(identified_rule_meta.get("output_tokens") or 0)

    # step4: calculate the target length for the shortening model to aim for (based on the lengths of the other options)
    min_length, max_length = calculate_length_range(options)

    # step5: shorten the longer option using the option shortener model to generate 5 candidates

    shortened_options_candidates_meta = generate_candidate_short_options(
        invocation_id=invocation_id,
        model=model,
        options=options,
        option_to_shorten=longer_option_text,
        syntactic_rule=identified_rule,
        min_target=min_length,  
        max_target=max_length,
        table_name="candidate_shortening_metadata",
        database_file= '../database/mcq_metadata.db'
    )  # List of lists, each inner list contains candidates for one longer option
    shortened_options_candidates = shortened_options_candidates_meta.get("candidates", [])
    # convert string representation back to list
    if isinstance(shortened_options_candidates, str):
        shortened_options_candidates = ast.literal_eval(shortened_options_candidates)

    input_tokens_accumulated += int(shortened_options_candidates_meta.get("input_tokens") or 0)
    output_tokens_accumulated += int(shortened_options_candidates_meta.get("output_tokens") or 0)

    if not shortened_options_candidates:
        return (mcq, {"input_tokens": input_tokens_accumulated, "output_tokens": output_tokens_accumulated})  # No candidates generated
    
    # step6: use the option ranker model to pick the best candidate, if none is good enough, keep the original option.

    candidate_selection_meta = select_best_candidate(
        invocation_id=invocation_id,
        model=model,
        options=options,
        option_to_shorten=longer_option_text,
        syntactic_rule=identified_rule,
        min_target=min_length,
        max_target=max_length,
        candidates=shortened_options_candidates,
        table_name="candidate_selection_metadata",
        database_file= '../database/mcq_metadata.db'
    )  # Returns the best candidate or None    
    best_candidate = candidate_selection_meta.get("best_candidate", None)
    input_tokens_accumulated += int(candidate_selection_meta.get("input_tokens") or 0)
    output_tokens_accumulated += int(candidate_selection_meta.get("output_tokens") or 0)
    
    if not best_candidate:
        return (mcq, {"input_tokens": input_tokens_accumulated, "output_tokens": output_tokens_accumulated})
    
    # step7: if a candidate is selected, update the MCQ with the new option text
    updated_mcq = update_mcq_with_new_option(mcq, best_candidate, longer_option_index)
    return (updated_mcq, {"input_tokens": input_tokens_accumulated, "output_tokens": output_tokens_accumulated})
