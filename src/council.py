import sqlite3
from sqlite3 import Error
def connect():
    conn = None
    try:
        conn = sqlite3.connect('council.db')
    except Error as e:
        print(e)
    return conn
def get_areas(conn):
    print('Areas available:')

    cur = conn.cursor()
    cur.execute("SELECT DISTINCT area FROM CallsForProposals")
    rows = cur.fetchall()
    for row in rows:
        print(row)
def get_income(conn, amount):
    cur = conn.cursor()
    try:
        amt = float(amount)
    except ValueError:
        print('invalid format, use a floating point number.')
    cur.execute("SELECT * FROM Account WHERE Balance > ? ORDER BY Balance", (amt,))
    rows = cur.fetchall()
    for row in rows:
        print(row)
# specify month, already have submitted one large proposal (request at least 20k OR have at least 10 participants)
def get_info_month(conn, month):
    cur = conn.cursor()

    query = """
    SELECT c.call_id, c.title
    FROM CallsForProposals c
    JOIN GrantProposals g ON c.call_id = g.call_id
    WHERE strftime('%m', c.app_deadline) = :user_specified_month
    AND (g.amount_requested > 20000 OR (
        SELECT COUNT(*) + 1
        FROM Collaborators col
        WHERE col.proposal_id = g.proposal_id
      ) > 10)
    GROUP BY c.call_id, c.title
    HAVING COUNT(DISTINCT g.proposal_id) > 0;"""
    cur.execute(query, (month,))
    rows = cur.fetchall()
    for row in rows:
        print(row)
# for user specified area, find largest proposal
def largest_money(conn):
    get_areas(conn)
    cur = conn.cursor()
    area = input('Area: ')

    query = """
    SELECT MAX (amount_requested) FROM GrantProposals G
    JOIN CallsForProposals C ON G.call_id = C.call_id
    WHERE C.area = ?"""
    cur.execute(query, (area,))

    rows = cur.fetchall()
    for row in rows:
        print(row)
def assign_reviewers(conn):
    cur = conn.cursor()
    # get reviewers
    query1 = """
    SELECT DISTINCT r_id FROM Reviewers 
        WHERE 
            conflicts_of_interest != (
                SELECT principal_investigator FROM GrantProposals
                WHERE proposal_id = ? 
            )
            AND conflicts_of_interest NOT IN (
                SELECT collaborator_id FROM Collaborators
                WHERE proposal_id = ?
            )
            AND r_id IN (
                SELECT reviewer_id FROM ReviewerAssignment
                GROUP BY reviewer_id
                HAVING COUNT(reviewer_id) < 3
            )
        ORDER BY r_id"""
    p_id = input('proposal id: ')
    cur.execute(query1, (p_id,p_id))
    
    rows = cur.fetchall()
    if len(rows) == 0:
        print('no reviewers available')
        return
    for row in rows:
        print(row)
    cur = conn.cursor()

    query2 = """
    INSERT INTO ReviewerAssignment (call_id, reviewer_id, deadline, status) 
    SELECT gp.call_id, ?, cp.app_deadline, 'Pending'
    FROM GrantProposals gp
    Left Join CallsForProposals cp ON cp.call_id = gp.call_id 
    WHERE 
        gp.proposal_id = ?"""
    r1 = input('reviewer 1: ')
    r2 = input('reviewer 2: ')
    r3 = input('reviewer 3: ')
    cur.execute(query2, (r1, p_id,))
    conn.commit()

    cur = conn.cursor()

    cur.execute(query2, (r2, p_id,))
    conn.commit()

    cur = conn.cursor()

    cur.execute(query2, (r3, p_id,))
    conn.commit()
    cur = conn.cursor()

    cur.execute("INSERT INTO Reviewers VALUES (?, ?)", (r1, r2))
    conn.commit()
    cur = conn.cursor()

    cur.execute("INSERT INTO Reviewers VALUES (?, ?)", (r1, r3))
    conn.commit()
    cur = conn.cursor()

    cur.execute("INSERT INTO Reviewers VALUES (?, ?)", (r2, r3))
    conn.commit()
    cur = conn.cursor()

    cur.execute("INSERT INTO Reviewers VALUES (?, ?)", (r2, r1))
    conn.commit()
    cur = conn.cursor()

    cur.execute("INSERT INTO Reviewers VALUES (?, ?)", (r3, r2))
    conn.commit()
    cur = conn.cursor()
    cur.execute("INSERT INTO Reviewers VALUES (?, ?)", (r3, r1))
    conn.commit()
    # update the table

def get_discrep(conn):
    query = """ 
    SELECT AVG(ABS(gp.amount_requested - gp.award_amount)) AS avg_discrepancy
    FROM GrantProposals gp
    JOIN CallsForProposals cp ON gp.call_id = cp.call_id
    WHERE cp.area = ?"""
    get_areas(conn)
    area = input('Area: ')
    cur = conn.cursor()
    cur.execute(query, (area,))
    rows = cur.fetchall()
    for row in rows:
        print(row)



def get_assgn(conn):
    query = """
    SELECT * FROM ReviewerAssignment
    WHERE reviewer_id = (
        SELECT r_id FROM Researchers
        WHERE 
            firstname = ?
            AND lastname = ? 
    )"""
    cur = conn.cursor()
    print('Reviewers:')
    cur.execute("SELECT DISTINCT Re.firstname, Re.lastname FROM Researchers Re JOIN Reviewers Rv ON Re.r_id = Rv.r_id")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    name = input('Name: ')
    firstname, lastname = name.split()

    cur.execute(query, (firstname, lastname,))
    rows = cur.fetchall()
    for row in rows:
        print(row)
def largest_award(conn, date):
    query = """
    SELECT * FROM GrantProposals
    WHERE 
        award_date < ?
        AND award_amount = (
            SELECT MAX(award_amount)
            FROM GrantProposals
            WHERE award_date < ?
        )"""
    cur = conn.cursor()
    cur.execute(query, (date, date,))
    rows = cur.fetchall()
    for row in rows:
        print(row)

def help():
    s = """
    <open> finds all the calls for proposals open during the month that have at least one large proposal\n
    <largest grant> finds the proposal that requests the most money\n
    <assignments> finds all the assignments for a given researcher\n
    <largest award> finds the proposal that was awarded the most money\n
    <assign reviewers> lets you assign reviewers to an assignment\n
    <discrepancies> finds the average discrepancy between amount requested vs amount rewards for a given area\n
    <quit> exits the program\n
    <help> opens the list of commands"""
    print(s)

def handle_input(conn):
    help()
    while True:
        user_input = input('Select an option: ')
        if user_input == 'quit':
            break
        elif user_input == 'largest grant':
            largest_money(conn)
        elif user_input == 'open':
            date = input('month MM:')
            get_info_month(conn, date)
        elif user_input == 'assignments':
            get_assgn(conn)
        elif user_input == 'assign reviewers':
            assign_reviewers(conn)
        elif user_input == 'discrepancies':
            get_discrep(conn)
        elif user_input == 'largest award':
            date = input('date YYYY-MM-DD:')
            largest_award(conn, date)
        elif user_input == 'help':
            help()
        else:
            print('invalid command, type <help> for list of commands')
            

def main():
    conn = connect()
    handle_input(conn)

if __name__ == '__main__':
    main()