import requests
import json
from sqlalchemy.orm.attributes import flag_modified
from database import SessionLocal, StudyProfile

def dictionary_lookup(word: str) -> str:
    """Busca a definição e a fonética da palavra via Free Dictionary API."""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()[0]
            phonetic = data.get("phonetic", "Não disponível")
            meanings = []
            for mean in data.get("meanings", [])[:2]:  # Pega no máximo os 2 primeiros usos (subst, verb...)
                pos = mean.get("partOfSpeech", "unknown")
                def_text = mean["definitions"][0]["definition"]
                meanings.append(f"[{pos}] {def_text}")
            return f"Definitions for '{word}': Phonetic {phonetic}. Meanings: {'; '.join(meanings)}"
        elif response.status_code == 404:
            return f"Word '{word}' not found in the dictionary."
    except Exception as e:
        return f"Error executing dictionary lookup: {e}"
    
    return f"Failed to get definition for '{word}'."

def save_flashcard(user_id: int, word: str, translation: str) -> str:
    """Salva no perfil do aluno uma palavra nova para ele revisar."""
    db = SessionLocal()
    try:
        profile = db.query(StudyProfile).filter_by(user_id=user_id).first()
        if not profile:
            profile = StudyProfile(user_id=user_id, flashcards=[])
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        # Garante que seja lista
        flashcards = profile.flashcards
        if flashcards is None:
            flashcards = []

        # Verifica se já não existe
        if not any(fc.get('word').lower() == word.lower() for fc in flashcards if 'word' in fc):
            flashcards.append({"word": word, "translation": translation})
            
            # Necessário para garantir que o SQLAlchemy detecte a mudança em colunas JSON
            profile.flashcards = flashcards
            flag_modified(profile, "flashcards")
            
            db.commit()
            return f"SYSTEM: Flashcard successfully saved ('{word}' -> '{translation}'). Tell the user it was saved."
        return f"SYSTEM: The flashcard for '{word}' already exists in profile."
    except Exception as e:
        db.rollback()
        return f"SYSTEM: Error saving flashcard: {str(e)}"
    finally:
        db.close()

def grammar_check(sentence: str) -> str:
    """Verifica erros gramaticais usando a API pública LanguageTool."""
    url = "https://api.languagetool.org/v2/check"
    data = {"text": sentence, "language": "en"}
    try:
        response = requests.post(url, data=data, timeout=5)
        if response.status_code == 200:
            matches = response.json().get("matches", [])
            if not matches:
                return f"Grammar check for '{sentence}': Correct phrase!"
            
            errors = []
            for match in matches:
                msg = match.get("message")
                replacements = [r["value"] for r in match.get("replacements", [])[:3]]
                replacements_text = f" Suggestions: {', '.join(replacements)}" if replacements else ""
                errors.append(f"Error: {msg}.{replacements_text}")
            
            return f"Grammar check results: {' | '.join(errors)}"
    except Exception as e:
        return f"Error executing grammar check: {e}"
    return "Failed to verify grammar."


# ─── Registro e Documentação de Ferramentas (Utilizado pelo ReAct) ────────

TOOLS_REGISTRY = {
    "dictionary_lookup": dictionary_lookup,
    "save_flashcard": save_flashcard,
    "grammar_check": grammar_check
}

TOOLS_DESCRIPTION = """Você tem acesso às seguintes ferramentas. Caso precise utilizar uma, você DEVE retornar ESTRITAMENTE o formato JSON descrito na regra!
[
  {
    "name": "dictionary_lookup",
    "description": "Busca o significado, fonética e classe gramatical de uma palavra em inglês.",
    "parameters": {"word": "<a palavra a ser buscada>"}
  },
  {
    "name": "save_flashcard",
    "description": "Salva uma nova palavra com sua tradução no perfil do aluno para revisões futuras. Use isso quando o aluno perguntar 'como se diz X' ou demonstrar que aprendeu uma palavra nova.",
    "parameters": {"word": "<palavra_em_ingles>", "translation": "<traducao_exata_em_portugues>"}
  },
  {
    "name": "grammar_check",
    "description": "Faz uma análise gramatical de uma frase fornecida em inglês. Use para validar as sentenças ou respostas que o aluno forneceu.",
    "parameters": {"sentence": "<a frase exata falada pelo aluno>"}
  }
]"""
