from flask import Flask, jsonify, request, g
from flask_cors import CORS

import json
import numpy as np
import os

import sqlite3

app = Flask(__name__)
CORS(app)

DATABASE = os.path.join(os.path.dirname(__file__), 'label_data.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def get_unlabeled_data():
    """ load unlabeled data into memory """

    # todo: optimize this process is necessary

    unlabeled_pairs = getattr(g, '_unlabeled', None)

    if unlabeled_pairs is None:

        db = get_db()
        c = db.cursor()

        c.execute('''SELECT pairs.id, pairs.task, pairs.left, pairs.right, 
                            pairs.left_feature, pairs.right_feature 
                     FROM pairs
                     WHERE NOT EXISTS (SELECT id FROM labels WHERE labels.id = pairs.id)''')

        content = c.fetchall()

        result = {}
        for row in content:
            data = {
                "id": row[0],
                "task": row[1],
                "left": json.loads(row[2]),
                "right": json.loads(row[3]),
                "left_feature": json.loads(row[4]),
                "right_feature": json.loads(row[5])
            }
        
            result[row[0]] = data

        unlabeled_pairs = g._unlabeled = result

    return unlabeled_pairs


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/fetch_pair', methods=['GET'])
def fetch_pair():
    """ fetch an unlabeled pair from the server """

    num_pairs = request.args.get('num_pairs', default=1, type=int)
    unlabeled_data = get_unlabeled_data()

    id_list = list(unlabeled_data.keys())

    rand_indices = np.random.choice(id_list, size=num_pairs, replace=False)

    if num_pairs > 1:
        return jsonify([unlabeled_data[i] for i in rand_indices])

    return jsonify(unlabeled_data[rand_indices[0]])


@app.route('/upload_label', methods=['POST'])
def upload_label():
    """ upload a label to the server """
    if not request or not 'id' in request.json or not 'label' in request.json:
        abort(400)

    db = get_db()
    c = db.cursor()

    tid = request.json['id']
    label = 0 if request.json['label'] == '=' else (-1 if request.json['label'] == '<' else 1)

    stmt = "INSERT INTO labels VALUES (?, ?)"
    c.execute(stmt, (tid, label))

    db.commit()

    # update the in memory copy
    get_unlabeled_data().pop(tid, None)

    return 'success'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
