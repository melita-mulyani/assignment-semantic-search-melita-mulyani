
import argparse
import os
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from google import genai


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_DIR / "data" / "ecommerce_faq_knowledge_base.csv"
INDEX_PATH = PROJECT_DIR / "artifacts" / "faq.index"

EMBEDDING_MODEL = "gemini-embedding-001"
LLM_MODEL = "gemini-3.5-flash-lite"

load_dotenv(PROJECT_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY tidak ditemukan. "
        "Pastikan file .env tersedia di folder utama proyek."
    )

client = genai.Client(api_key=API_KEY)


# ============================================================
# 2. INGEST: LOAD AND PROCESS KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():
    """Load FAQ data and prepare text for embedding."""

    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "faq_id",
        "category",
        "question",
        "answer",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Kolom CSV tidak ditemukan: {sorted(missing_columns)}"
        )

    if df[list(required_columns)].isnull().any().any():
        raise ValueError(
            "Knowledge base memiliki nilai kosong pada kolom wajib."
        )

    # Gabungkan pertanyaan dan jawaban sebagai dokumen retrieval.
    df["content"] = (
        "Q: " + df["question"].astype(str)
        + " A: " + df["answer"].astype(str)
    )

    print(f"Jumlah FAQ: {len(df)}")
    print(f"Jumlah kategori: {df['category'].nunique()}")
    print(f"Kolom tersedia: {list(df.columns)}")

    return df


# ============================================================
# 3. EMBED: GENERATE EMBEDDINGS
# ============================================================

def get_embedding(text):
    """Generate embedding using Gemini Embeddings API."""

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    return result.embeddings[0].values


# ============================================================
# 4. STORE: BUILD AND SAVE FAISS INDEX
# ============================================================

def build_faiss_index(df):
    """Generate FAQ embeddings and save the FAISS index."""

    print(
        f"\nMembuat embedding untuk {len(df)} FAQ. "
        "Proses ini menggunakan Gemini API..."
    )

    vectors = [
        get_embedding(content)
        for content in df["content"].tolist()
    ]

    embeddings = np.asarray(vectors, dtype="float32")

    if embeddings.ndim != 2 or len(embeddings) != len(df):
        raise ValueError(
            "Shape embedding tidak sesuai dengan jumlah FAQ."
        )

    print(f"Shape embeddings: {embeddings.shape}")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_PATH))

    print(f"FAISS index disimpan: {INDEX_PATH}")
    print(f"Jumlah vector: {index.ntotal}")
    print(f"Dimensi embedding: {embeddings.shape[1]}")

    return index


def load_or_build_index(df, rebuild=False):
    """Load saved FAISS index or build a new one."""

    if rebuild or not INDEX_PATH.exists():
        return build_faiss_index(df)

    index = faiss.read_index(str(INDEX_PATH))

    # Validasi jumlah vector terhadap knowledge base.
    if index.ntotal != len(df):
        print(
            "Jumlah vector tidak cocok dengan CSV. "
            "Membuat ulang index..."
        )
        return build_faiss_index(df)

    # Validasi dimensi embedding.
    if index.d != len(get_embedding_dimension_sample()):
        print(
            "Dimensi index tidak sesuai. "
            "Membuat ulang index..."
        )
        return build_faiss_index(df)

    print(f"Memuat FAISS index: {INDEX_PATH}")
    print(f"Jumlah vector: {index.ntotal}")

    return index


def get_embedding_dimension_sample():
    """Get the configured embedding vector dimension."""

    sample = get_embedding("Tes dimensi embedding")
    return sample


# ============================================================
# 5. RETRIEVE: SEMANTIC SEARCH
# ============================================================

def semantic_search(query, df, index, top_k=3):
    """Retrieve the top-k FAQ entries closest to the query."""

    if not query or not query.strip():
        return []

    if index.ntotal == 0:
        return []

    query_vector = np.asarray(
        [get_embedding(query)],
        dtype="float32",
    )

    k = min(max(1, top_k), index.ntotal)

    distances, indices = index.search(query_vector, k)

    results = []

    for rank, (distance, idx) in enumerate(
        zip(distances[0], indices[0]),
        start=1,
    ):
        if idx < 0:
            continue

        row = df.iloc[int(idx)]

        results.append(
            {
                "rank": rank,
                "faq_id": row["faq_id"],
                "category": row["category"],
                "question": row["question"],
                "answer": row["answer"],
                "distance": float(distance),
            }
        )

    return results


# ============================================================
# 6. PROMPT DESIGN + LLM INTEGRATION
# ============================================================

def build_prompt(query, retrieved_faqs):
    """Build a structured Persona, Task, Context, Format prompt."""

    context = "\n\n".join(
        f"FAQ ID: {faq['faq_id']}\n"
        f"Kategori: {faq['category']}\n"
        f"FAQ: {faq['question']}\n"
        f"Jawaban: {faq['answer']}"
        for faq in retrieved_faqs
    )

    prompt = f"""
PERSONA:
Kamu adalah asisten customer service e-commerce
yang ramah, sopan, dan membantu.

TASK:
Jawab pertanyaan pengguna hanya berdasarkan informasi
dalam konteks FAQ yang diberikan.

Aturan:
1. Jangan mengarang informasi atau kebijakan.
2. Jangan menggunakan pengetahuan umum di luar konteks FAQ.
3. Jika konteks tidak memuat jawaban yang relevan,
   katakan bahwa informasi belum tersedia dan sarankan
   pengguna menghubungi Customer Service.
4. Jangan menganggap FAQ teratas selalu relevan.
5. Gunakan informasi FAQ yang benar-benar menjawab pertanyaan.

CONTEXT - FAQ RELEVAN:
{context}

PERTANYAAN PENGGUNA:
{query}

FORMAT:
Berikan jawaban dalam Bahasa Indonesia yang jelas,
ringkas, ramah, dan langsung menjawab pertanyaan.
"""

    return prompt


def generate_answer(query, retrieved_faqs):
    """Generate a grounded answer with graceful API error handling."""

    if not retrieved_faqs:
        return (
            "Maaf, saya belum menemukan informasi yang relevan. "
            "Silakan hubungi Customer Service untuk bantuan lebih lanjut."
        )

    prompt = build_prompt(query, retrieved_faqs)

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
        )

        return response.text or "Maaf, jawaban belum dapat dibuat."

    except Exception as exc:
        print(f"\n[Peringatan] Gemini API gagal: {exc}")

        return (
            "Maaf, layanan pembuatan jawaban sedang tidak tersedia. "
            "Silakan coba kembali beberapa saat lagi."
        )


# ============================================================
# 7. TESTING: FIVE REPRESENTATIVE QUERIES
# ============================================================

def run_tests(df, index):
    """Test direct questions, paraphrases, and an unknown question."""

    test_queries = [
        # Pertanyaan yang jawabannya tersedia.
        "Bagaimana cara melacak pesanan saya?",

        # Parafrasa dari FAQ pembatalan.
        "Saya ingin membatalkan order yang sudah dibuat.",

        # Parafrasa dari FAQ pengiriman.
        "Kenapa paket saya terlambat sampai?",

        # Pertanyaan pembayaran dengan sinonim.
        "Apakah saya bisa membayar belanjaan secara angsuran?",

        # Informasi yang tidak tersedia secara spesifik.
        "Apakah tersedia instalasi produk di rumah?",
    ]

    for number, query in enumerate(test_queries, start=1):
        print("\n" + "=" * 70)
        print(f"TEST {number}: {query}")

        try:
            results = semantic_search(
                query,
                df,
                index,
                top_k=3,
            )

            print("\nFAQ YANG DITEMUKAN:")

            for faq in results:
                print(
                    f"\nRank: {faq['rank']}"
                    f"\nFAQ ID: {faq['faq_id']}"
                    f"\nKategori: {faq['category']}"
                    f"\nDistance: {faq['distance']:.4f}"
                    f"\nPertanyaan: {faq['question']}"
                    f"\nJawaban FAQ: {faq['answer']}"
                )

            print("\nJAWABAN LLM:")

            answer = generate_answer(query, results)
            print(answer)

            print("\nSUMBER FAQ:")

            if results:
                for faq in results:
                    print(
                        f"- ID {faq['faq_id']}: "
                        f"{faq['question']}"
                    )
            else:
                print("- Tidak ada FAQ yang ditemukan.")

        except Exception as exc:
            # Agar error satu query tidak menghentikan query berikutnya.
            print(
                f"[Peringatan] Pengujian query ini gagal: {exc}"
            )

        print("\n" + "-" * 70)


# ============================================================
# 8. MAIN PROGRAM
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Semantic Search and LLM Application "
            "untuk FAQ e-commerce"
        )
    )

    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help=(
            "Buat ulang embeddings dan FAISS index "
            "menggunakan Gemini API"
        ),
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Jalankan lima query pengujian",
    )

    parser.add_argument(
        "--query",
        type=str,
        help="Ajukan satu pertanyaan kepada sistem",
    )

    args = parser.parse_args()

    df = load_knowledge_base()

    index = load_or_build_index(
        df,
        rebuild=args.rebuild_index,
    )

    if args.test:
        run_tests(df, index)

    elif args.query:
        results = semantic_search(
            args.query,
            df,
            index,
            top_k=3,
        )

        print("\nFAQ YANG DITEMUKAN:")

        for faq in results:
            print(
                f"Rank {faq['rank']} | "
                f"ID={faq['faq_id']} | "
                f"Distance={faq['distance']:.4f} | "
                f"{faq['question']}"
            )

        print("\nJAWABAN:")

        print(generate_answer(args.query, results))

    else:
        print("\nIndex siap digunakan.")
        print(
            'Contoh: python src\\semantic_search.py '
            '--query "Bagaimana cara melacak pesanan?"'
        )
        print(
            "Pengujian: python src\\semantic_search.py --test"
        )


if __name__ == "__main__":
    main()
