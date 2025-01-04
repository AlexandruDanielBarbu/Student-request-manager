from sentence_transformers import SentenceTransformer, util
import os
import torch
import json

model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')
if not os.path.exists('models/sbert_model'):
    model.save('models/sbert_model')


def compute_similarity(question, questions):
    """
    Computes cosine similarity between two sentences.

    Args:
        sentence1 (str): First sentence.
        sentence2 (str): Second sentence.

    Returns:
        float: Cosine similarity score between -1 and 1.
    """
    embedding1 = model.encode(question, convert_to_tensor=True)
    embedding2 = model.encode(questions, convert_to_tensor=True)

    similarity = util.pytorch_cos_sim(embedding1, embedding2)
    if similarity.max().item() >= 0.5:
        return similarity.argmax().item(), similarity.max().item()
    return None, similarity.max().item()


def get_faqs(file_name: str):
    with open(file_name, 'r') as file:
        data = json.load(file)
    key = file_name.split('.')[0]
    q_list = [x['question'] for x in data[key]]
    ans_list = [x['answer'] for x in data[key]]
    return data['faq'], q_list, ans_list


def add_rejected_question(rejected_question, answer):
    rejected_file = 'rejected_faq.json'
    idx_faq = -1

    if os.path.exists(rejected_file):
        with open(rejected_file, 'r') as file:
            rejected_data = json.load(file)
    else:
        rejected_data = {"rejected_faq": []}

    if len(rejected_data["rejected_faq"]) > 0:
        rej_qlist = [x["question"] for x in rejected_data["rejected_faq"]]
        idx, corr = compute_similarity(rejected_question, rej_qlist)
    else:
        idx = None

    if idx == None:
        rejected_data["rejected_faq"].append(
            {"question": rejected_question, "answer": answer, "frequency": 1}
        )
    else:
        rejected_data["rejected_faq"][idx]["frequency"] += 1
        if rejected_data["rejected_faq"][idx]["frequency"] >= 3:
            idx_faq = idx

    with open(rejected_file, 'w') as file:
        json.dump(rejected_data, file, indent=4)

    return idx_faq


def remove_rejected_question(idx_faq, q_list, ans_list):
    file_name = 'rejected_faq.json'

    with open(file_name, 'r') as file:
        data = json.load(file)

    rez = data["rejected_faq"][idx_faq]
    del rez["frequency"]
    add_faq(rez)
    q_list.append(rez["question"])
    ans_list.append(rez["answer"])
    data["rejected_faq"].pop(idx_faq)

    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)


def add_faq(rez):

    file_name = 'faq.json'

    with open(file_name, 'r') as file:
        data = json.load(file)

    if isinstance(data["faq"], list) and rez not in data["faq"]:
        data["faq"].append(rez)

    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)


def main():
    faqs, question_list, answer_list = get_faqs("faq.json")

    while True:
        question = input()

        if question == "exit":
            break

        best_match_idx, corr = compute_similarity(question, question_list)
        try:
            print(f"{corr:.2f}\n{answer_list[best_match_idx]}")
        except TypeError:
            print(f"{corr:.2f}\nNo match found\nHuman answer: ", end="")
            human_answer = input()
            idx_faq = add_rejected_question(question, human_answer)
            if idx_faq != -1:
                remove_rejected_question(idx_faq, question_list, answer_list)


if __name__ == "__main__":
    main()
