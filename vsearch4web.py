from threading import Thread
import os
import subprocess

import flask
from flask import Flask, render_template, request, session
from flask import copy_current_request_context

from DBcm import UseDatabase, ConnectionError, CredentialsError, SQLError
from checker import check_logged_in

app = Flask(__name__)

app.config['dbconfig'] = {
    'host':'127.0.0.1',
    'user':'vsearch',
    'password':'passwordvs',
    'database':'vsearchlogDB',
    #'auth_plugin': 'caching_sha2_password'
}

def search4letters(phrase:str, letters:str='aoieu') -> str:
    stream = subprocess.Popen(['py', 'search4letters.py', phrase, letters],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    stdout, stderr = stream.communicate()
    return stdout
    # print('py search4letters.py {} {}'.format(phrase, letters))
    # stream = os.popen('py search4letters.py {} {}'.format(phrase, letters))
    # output = stream.read()
    # return output
    # return set(letters).intersection(set(phrase))

                          
@app.route('/login')
def do_login() -> str:
    session['logged_in']=True
    return "You are logged in"
    

@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')
    return "You are now logged out"



@app.route('/search4', methods=['POST'])
def do_search() -> 'html':

    @copy_current_request_context
    def log_request(req: 'flask_request', res: str) -> None:
        """ Log details of the web request and the results. """  
        try:
            with UseDatabase(app.config['dbconfig']) as cursor:
                first_query = """CREATE TABLE IF NOT EXISTS log (
                                    id int auto_increment primary key,
                                    phrase varchar(128) not null,
                                    letters varchar(32) not null,
                                    results varchar(64) not null)"""
                cursor.execute(first_query)
                # temp = """INSERT INTO log(phrase, letters, results)
                # VALUES("%s", "%s", "%s")"""
                # query = temp % (req.form['phrase'], res.strip(), req.form['letters'])
                # print(query)
                # cursor.execute(query)
                query = """insert into log
                                (phrase, letters, results)
                                values
                                (%s, %s, %s)"""
                cursor.execute(query, (req.form['phrase'], res, req.form['letters'],))
                


        except ConnectionError as err:
            print('Is your databse switched on? Error:', str(err))
        except CredentialsError as err:
            print('User-id/Password issues. Error:', str(err))
        except SQLError as err:
            print('Is your query correct?', str(err))
        except Exception as err:
            print('Something wrong:', str(err))
        return 'Error'
    
    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are your results:'
    results = str(search4letters(phrase, letters))   
    try:
        t = Thread(target=log_request, args=(request, results))
        t.start() 
    except Exception as err:
        print("Something went wrong:", str(err))
    return render_template('results.html',
                           the_phrase=phrase,
                           the_letters=letters,
                           the_title=title,
                           the_results=results,)


@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
    return render_template('entry.html',
                           the_title='Welcome to search4letters on the web!')


@app.route('/viewlog')
@check_logged_in
def view_log() -> 'html':
    """ Display the contents of the log file as a HTML table. """
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            query = """select phrase, letters, results
                       from log"""
            cursor.execute(query)
            contents = cursor.fetchall()
            
        titles = ('Phrase', 'letters', 'Results')
        return render_template('viewlog.html',
                               the_title='View Log',
                               the_row_titles=titles,
                               the_data=contents,)
    except ConnectionError as err:
        print('Is your databse switched on? Error:', str(err))
    except CredentialsError as err:
        print('User-id/Password issues. Error:', str(err))
    except SQLError as err:
        print('Is your query correct?', str(err))
    except Exception as err:
        print('Something wrong:', str(err))
    return 'Error'





app.secret_key="YouMayGuessMyKey"

if __name__ == '__main__':
    app.run(debug=True)




