from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
from database import init_db, get_db
from dotenv import load_dotenv
import os
import hashlib
import random
import string
from datetime import datetime
import ast

# ====================== KONFIGURATION ======================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super-langer-geheimer-key-2026-lehrerecho')


# Entwickler Zugang
DEV_USER = os.getenv('DEV_USERNAME')
DEV_PASS = os.getenv('DEV_PASSWORD')

if not DEV_USER or not DEV_PASS:
    DEV_USER = "Theodor.Schwehm"
    DEV_PASS = "HG.jt.700"

print("✅ LehrerEcho mit CSRF-Schutz gestartet")

# ====================== BAD_WORDS (große Liste) ======================
BAD_WORDS = [
    "arsch", "fotze", "hurensohn", "fick", "scheiß", "idiot", "dumm", "bitch", "fuck", "shit", "arschloch",
    "hure", "nutte", "schlampe", "wichser", "bastard", "spast", "behindert", "depp", "trottel", "vollidiot",
    "penner", "loser", "opfer", "lutscher", "verpiss", "verreck", "kacke", "kackbratze", "scheisskerl",
    "miststück", "drecksau", "sausack", "dreckskerl", "mistkerl", "scheissfresse", "dreckfresse", "arschgesicht",
    "fotzengesicht", "wichsgriffel", "spermagesicht", "pissnelke", "kackfresse", "mülltonne", "müllsack",
    "menschenmüll", "abschaum", "untermensch", "missgeburt", "fratze", "visage", "fettklops", "fettarsch",
    "fettwanst", "fettbacke", "hässlich", "mongol", "downie", "retard", "behindi", "krüppel", "zwerg",
    "schwuchtel", "schwule", "lesbe", "transe", "faggot", "simp", "incel", "beta", "cuck", "noob", "n00b",
    "verfickte", "verpisste", "verfluchte", "dreckstück", "saubratze", "schweinefresse", "hundesohn",
    "tierficker", "pädophil", "vergewaltiger", "kinderschänder", "mörder", "verräter", "spitzel",
    "schwanzlutscher", "arschlecker", "fotzenlecker", "tittenlecker", "cunt", "motherfucker", "sonofabitch",
    "dickhead", "pussy", "cock", "cocksucker", "wanker", "twat", "slag", "whore", "slut", "bullshit",
    "douchebag", "jackass", "dumbass", "shithead", "fuckhead", "asshole", "retarded", "fucking idiot",
    "fucking moron", "fucking loser", "worthless", "pathetic", "disgusting", "ugly", "freak", "monster",
    "abomination", "garbage", "trash", "scum", "vermin", "parasite", "leech", "cancer", "aids", "virus",
    "plague", "rotten", "putrid", "foul", "stinky", "piss", "crap", "turd", "diarrhea", "boob", "tit",
    "ass", "butt", "dick", "vagina", "anus", "fart", "cum", "jizz", "spunk", "gangbang", "orgy", "bukkake",
    "facial", "golden shower", "cuckold", "simp", "incel", "virgin", "neckbeard", "basement dweller",
    "mama's boy", "entitled", "snowflake", "libtard", "fettmonster", "koksnase", "junkie", "alki", "säufer",
    "stricher", "hurekind", "bastardsohn", "verhurte", "missgeburt", "ausgeburt", "dreckhure", "drecknutte"
]

def get_semester():
    now = datetime.now()
    year = now.year
    return f"{year}-1" if now.month <= 6 else f"{year}-2"

def generate_key(length):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def contains_bad_word(text):
    if not text:
        return False
    return any(word in text.lower() for word in BAD_WORDS)

# ====================== ALLGEMEIN ======================
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == DEV_USER and password == DEV_PASS:
            session['user_id'] = 0
            session['role'] = 'developer'
            session['name'] = 'Theodor Schwehm'
            flash("Willkommen zurück, Entwickler!", "success")
            return redirect(url_for('developer_dashboard'))
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['full_name']
            
            if user['role'] == 'director':
                return redirect(url_for('director_dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
        
        flash("Falsche Zugangsdaten", "error")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        key = request.form.get('key')
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        
        if password != password2:
            flash("Passwörter stimmen nicht überein!", "error")
            return render_template('register.html')
        
        db = get_db()
        
        if role == 'director':
            skey = db.execute("SELECT * FROM school_keys WHERE key = ? AND used = 0", (key,)).fetchone()
            if not skey:
                flash("Ungültiger Schulschlüssel!", "error")
                return render_template('register.html')
            user_role = 'director'
            class_name = None
        else:
            pkey = db.execute("SELECT * FROM person_keys WHERE key = ? AND used = 0", (key,)).fetchone()
            if not pkey or pkey['full_name'].lower() != full_name.lower():
                flash("Ungültiger Schlüssel oder falscher Name!", "error")
                return render_template('register.html')
            user_role = role
            class_name = pkey['class_name']
        
        username = full_name.strip().replace(" ", ".").replace("..", ".")
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        
        db.execute("INSERT INTO users (username, password, role, full_name, class_name) VALUES (?,?,?,?,?)",
                   (username, hashed_pw, user_role, full_name, class_name))
        
        if role == 'director':
            db.execute("UPDATE school_keys SET used = 1 WHERE key = ?", (key,))
        else:
            db.execute("UPDATE person_keys SET used = 1 WHERE key = ?", (key,))
        
        db.commit()
        flash(f"Account erstellt! Benutzername: <strong>{username}</strong>", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ====================== ENTWICKLER ======================
@app.route('/developer')
def developer_dashboard():
    if session.get('role') != 'developer':
        return redirect(url_for('login'))
    
    db = get_db()
    school_keys = db.execute("SELECT * FROM school_keys ORDER BY created_at DESC").fetchall()
    person_keys = db.execute("SELECT * FROM person_keys ORDER BY created_at DESC").fetchall()
    blocked = db.execute("SELECT * FROM blocked_evaluations ORDER BY created_at DESC").fetchall()
    
    phase = db.execute("SELECT value FROM settings WHERE key = 'evaluation_active'").fetchone()
    evaluation_active = phase['value'] == 'true' if phase else False
    
    return render_template('developer/dashboard.html', 
                         school_keys=school_keys, 
                         person_keys=person_keys, 
                         blocked=blocked,
                         evaluation_active=evaluation_active)

@app.route('/developer/create_school_key', methods=['POST'])
def create_school_key():
    if session.get('role') != 'developer':
        return redirect(url_for('login'))
    max_users = int(request.form.get('max_users', 1))
    key = generate_key(18)
    db = get_db()
    db.execute("INSERT INTO school_keys (key, max_users, for_role) VALUES (?,?,?)", 
               (key, max_users, "director"))
    db.commit()
    flash(f"✅ Schulschlüssel erstellt: <strong>{key}</strong>", "success")
    return redirect(url_for('developer_dashboard'))

@app.route('/developer/start_evaluation', methods=['POST'])
def start_evaluation():
    if session.get('role') != 'developer':
        return redirect(url_for('login'))
    db = get_db()
    db.execute("UPDATE settings SET value = 'true' WHERE key = 'evaluation_active'")
    db.commit()
    flash("▶️ Bewertungsphase wurde GESTARTET", "success")
    return redirect(url_for('developer_dashboard'))

@app.route('/developer/stop_evaluation', methods=['POST'])
def stop_evaluation():
    if session.get('role') != 'developer':
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute("UPDATE settings SET value = 'false' WHERE key = 'evaluation_active'")
    db.commit()
    
    flash("⏹️ Bewertungsphase wurde BEENDET. Dieses Halbjahr ist jetzt abgeschlossen.", "error")
    return redirect(url_for('developer_dashboard'))

# ====================== DIREKTOR ======================
@app.route('/director')
def director_dashboard():
    if session.get('role') != 'director':
        return redirect(url_for('login'))
    db = get_db()
    teacher_keys = db.execute("SELECT * FROM person_keys WHERE role = 'teacher' ORDER BY created_at DESC").fetchall()
    student_keys = db.execute("SELECT * FROM person_keys WHERE role = 'student' ORDER BY created_at DESC").fetchall()
    return render_template('director/dashboard.html', teacher_keys=teacher_keys, student_keys=student_keys)

@app.route('/director/create_keys', methods=['POST'])
def create_keys():
    if session.get('role') != 'director':
        return redirect(url_for('login'))
    role = request.form.get('role')
    names_text = request.form.get('names', '').strip()
    count = int(request.form.get('count', 5))
    if not names_text:
        flash("Bitte gib Namen ein!", "error")
        return redirect(url_for('director_dashboard'))
    
    db = get_db()
    names_list = [line.strip() for line in names_text.split('\n') if line.strip()]
    created_count = 0
    for line in names_list[:count]:
        if role == 'student' and ' ' in line:
            parts = line.rsplit(' ', 1)
            full_name = parts[0].strip()
            class_name = parts[1].strip() if len(parts) > 1 else ""
        else:
            full_name = line.strip()
            class_name = ""
        key = generate_key(12)
        db.execute("INSERT INTO person_keys (key, full_name, role, class_name) VALUES (?,?,?,?)",
                   (key, full_name, role, class_name))
        created_count += 1
    db.commit()
    flash(f"{created_count} {'Schüler' if role == 'student' else 'Lehrer'}-Schlüssel erstellt!", "success")
    return redirect(url_for('director_dashboard'))

# ====================== LEHRER ======================
@app.route('/teacher')
def teacher_dashboard():
    if session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    db = get_db()
    teacher_id = session['user_id']
    current_semester = get_semester()
    
    # Aktuelle Bewertungen (laufendes Halbjahr)
    current_evals = db.execute("""
        SELECT * FROM evaluations 
        WHERE teacher_id = ? AND semester = ?
        ORDER BY created_at DESC
    """, (teacher_id, current_semester)).fetchall()
    
    # Vorherige Halbjahre
    previous_evals = db.execute("""
        SELECT * FROM evaluations 
        WHERE teacher_id = ? AND semester != ?
        ORDER BY semester DESC, created_at DESC
    """, (teacher_id, current_semester)).fetchall()
    
    return render_template('teacher/dashboard.html', 
                         current_evals=current_evals,
                         previous_evals=previous_evals,
                         current_semester=current_semester)
# ====================== SCHÜLER ======================
@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    db = get_db()
    teachers = db.execute("SELECT id, full_name FROM users WHERE role = 'teacher'").fetchall()
    
    my_evaluations = db.execute("""
        SELECT e.*, u.full_name as teacher_name 
        FROM evaluations e
        JOIN users u ON e.teacher_id = u.id
        WHERE e.student_id = ?
        ORDER BY e.created_at DESC
    """, (session['user_id'],)).fetchall()
    
    # Bewertungsphase-Status holen
    phase = db.execute("SELECT value FROM settings WHERE key = 'evaluation_active'").fetchone()
    evaluation_active = phase['value'] == 'true' if phase else False
    
    return render_template('student/dashboard.html', 
                         teachers=teachers, 
                         my_evaluations=my_evaluations,
                         evaluation_active=evaluation_active)
@app.route('/student/rate/<int:teacher_id>', methods=['GET', 'POST'])
def rate_teacher(teacher_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    db = get_db()
    teacher = db.execute("SELECT full_name FROM users WHERE id = ?", (teacher_id,)).fetchone()
    
    if request.method == 'POST':
        phase = db.execute("SELECT value FROM settings WHERE key = 'evaluation_active'").fetchone()
        if not phase or phase['value'] != 'true':
            flash("Die Bewertungsphase ist derzeit geschlossen!", "error")
            return redirect(url_for('student_dashboard'))
        
        semester = get_semester()
        student_id = session['user_id']
        
        already = db.execute("SELECT id FROM evaluations WHERE teacher_id = ? AND student_id = ? AND semester = ?", 
                           (teacher_id, student_id, semester)).fetchone()
        if already:
            flash("Du hast diesen Lehrer bereits bewertet!", "error")
            return redirect(url_for('student_dashboard'))
        
        friendliness = int(request.form.get('friendliness') or 0)
        fairness = int(request.form.get('fairness') or 0)
        patience = int(request.form.get('patience') or 0)
        teaching_quality = int(request.form.get('teaching_quality') or 0)
        organization = int(request.form.get('organization') or 0)
        
        comment_f = request.form.get('comment_f', '').strip()
        comment_fa = request.form.get('comment_fa', '').strip()
        comment_p = request.form.get('comment_p', '').strip()
        comment_t = request.form.get('comment_t', '').strip()
        comment_o = request.form.get('comment_o', '').strip()
        
        blocked = contains_bad_word(comment_f) or contains_bad_word(comment_fa) or contains_bad_word(comment_p) or contains_bad_word(comment_t) or contains_bad_word(comment_o)
        
        if blocked:
            raw_data = str({
                'teacher_id': teacher_id, 'student_id': student_id, 'semester': semester,
                'friendliness': friendliness, 'fairness': fairness, 'patience': patience,
                'teaching_quality': teaching_quality, 'organization': organization,
                'comment_f': comment_f, 'comment_fa': comment_fa, 'comment_p': comment_p,
                'comment_t': comment_t, 'comment_o': comment_o
            })
            db.execute("INSERT INTO blocked_evaluations (raw_data) VALUES (?)", (raw_data,))
            flash("Deine Bewertung wird geprüft.", "warning")
        else:
            db.execute("""INSERT INTO evaluations 
                (teacher_id, student_id, semester, friendliness, fairness, patience, teaching_quality, organization,
                 comment_f, comment_fa, comment_p, comment_t, comment_o)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (teacher_id, student_id, semester, friendliness, fairness, patience, teaching_quality, organization,
                 comment_f, comment_fa, comment_p, comment_t, comment_o))
            flash("Bewertung erfolgreich abgegeben!", "success")
        
        db.commit()
        return redirect(url_for('student_dashboard'))
    
    return render_template('student/rate.html', teacher=teacher)

# ====================== LÖSCHEN & BLOCKIERTE ======================
@app.route('/student/delete_evaluation/<int:eval_id>', methods=['POST'])
def delete_evaluation(eval_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    db = get_db()
    db.execute("DELETE FROM evaluations WHERE id = ? AND student_id = ?", (eval_id, session['user_id']))
    db.commit()
    flash("Bewertung gelöscht.", "success")
    return redirect(url_for('student_dashboard'))

@app.route('/developer/approve_blocked/<int:eval_id>', methods=['POST'])
def approve_blocked(eval_id):
    if session.get('role') != 'developer':
        return redirect(url_for('login'))
    db = get_db()
    blocked = db.execute("SELECT * FROM blocked_evaluations WHERE id = ?", (eval_id,)).fetchone()
    if blocked:
        try:
            data = ast.literal_eval(blocked['raw_data'])
            db.execute("""INSERT INTO evaluations 
                (teacher_id, student_id, semester, friendliness, fairness, patience, teaching_quality, organization,
                 comment_f, comment_fa, comment_p, comment_t, comment_o, status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?, 'approved')""",
                (data.get('teacher_id'), data.get('student_id'), data.get('semester'),
                 data.get('friendliness', 0), data.get('fairness', 0), data.get('patience', 0),
                 data.get('teaching_quality', 0), data.get('organization', 0),
                 data.get('comment_f', ''), data.get('comment_fa', ''), 
                 data.get('comment_p', ''), data.get('comment_t', ''), data.get('comment_o', '')))
            db.execute("DELETE FROM blocked_evaluations WHERE id = ?", (eval_id,))
            db.commit()
            flash("✅ Bewertung zugelassen!", "success")
        except:
            flash("Fehler beim Zulassen.", "error")
    return redirect(url_for('developer_dashboard'))

@app.route('/developer/reject_blocked/<int:eval_id>', methods=['POST'])
def reject_blocked(eval_id):
    if session.get('role') != 'developer':
        return redirect(url_for('login'))
    db = get_db()
    db.execute("DELETE FROM blocked_evaluations WHERE id = ?", (eval_id,))
    db.commit()
    flash("❌ Bewertung verweigert.", "error")
    return redirect(url_for('developer_dashboard'))

if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print("🚀 LehrerEcho läuft")
    print("=" * 60)
    
    # Wichtig für Render!
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)