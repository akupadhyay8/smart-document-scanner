from sentence_transformers import SentenceTransformer, util

# Load a pre-trained model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_local_embedding(text):
    return model.encode(text, convert_to_tensor=True)

def cosine_similarity_local(emb1, emb2):
    return util.pytorch_cos_sim(emb1, emb2).item()
