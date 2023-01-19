import io
import base64
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from flask import Flask, render_template
from settings.config_db import DATABASE, USER, PASS, HOST

app = Flask(__name__)


def generate_plot():
    # create a connection to the database
    engine = create_engine(f'mysql+mysqlconnector://{USER}:{PASS}@{HOST}/{DATABASE}', echo=True)

    # execute a query to retrieve the data
    result = engine.execute("SELECT ali, cb, currency_difference, date FROM currency")

    # extract the data from the result set
    ali = []
    cb = []
    difference = []
    date = []

    for row in result:
        ali.append(row[0])
        cb.append(row[1])
        difference.append(row[2])
        date.append(row[3].strftime('%d-%m'))
        print(date)

    # close the connection
    result.close()

    # create a line plot of the data
    fig, ax1 = plt.subplots(figsize=(9, 9))
    ax2 = ax1.twinx()
    ax1.plot(date, ali, 'g-')
    ax1.plot(date, cb, 'b-')
    ax2.plot(date, difference, 'r-')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Ali and CB Currency', color='g', fontsize=12)
    ax2.set_ylabel('Difference', color='r', fontsize=12)
    ax1.set_ylim(0, 200)

    # convert the plot to a png image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read()).decode()
    data = 'data:image/png;base64,' + string
    plt.close()
    return data


@app.route('/')
def index():
    return render_template('index.html', plot_url=generate_plot())


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(host='192.168.31.178')

# # create a connection to the database
# engine = create_engine(f'mysql+mysqlconnector://{USER}:{PASS}@{HOST}/{DATABASE}', echo=False)
#
# # execute a query to retrieve the data
# result = engine.execute("SELECT ali, cb, currency_difference, date FROM currency")
#
# for row in result:
#     print(row)
# result.close()
