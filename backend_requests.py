from app import app
import json
import requests
from flask import request, session, make_response, jsonify, Response, render_template, redirect
from database_config import *

def error(comment):
    result = dict()
    result['status'] = 'Error'
    result['message'] = comment
    return jsonify(result)

@app.route("/", methods=['GET'])
def index_get():
    if 'login' not in session:
        return redirect('/login')
    return render_template('index.html')


@app.route("/login", methods=['GET'])
def login_get():
    return render_template('auth.html')


@app.route("/mygroups", methods=['GET'])
def my_groups():
    if 'login' not in session:
        return redirect('/login')
    return render_template('my_groups.html')



@app.route("/logout", methods=['GET'])
def logout_get():
    global session
    session = {}
    return redirect('/')


@app.route('/error')
@app.errorhandler(404)
def not_found_page(error):
    if 'login' not in session:
        return redirect('/')
    return '404',    404

###  API


@app.route("/req/auth", methods=['POST'])
def req_auth_post():
    req = json.loads(request.data)
    result = dict()
    result['status'] = None
    result['message'] = None

    if 'login' not in req or 'password' not in req:
        return error('Недостаточно данных')

    account = AccountsDB.get_by_login(req['login'])
    if account is None:
        return error('Пользователя не существует')

    if account['password'] != req['password']:
        return error('Неправильный пароль')

    print('Пользователь вошёл в систему', account['login'])

    result['status'] = 'Ok'
    result['message'] = ''

    session['account_id'] = account['account_id']
    session['login'] = account['login']

    return jsonify(result)



@app.route("/req/reg", methods=['POST'])
def req_reg_post():
    result = dict()
    result['status'] = None
    result['message'] = None


    #print(request.data)

    try:
        req = json.loads(request.data)
        if str(type(req)) != "<class 'dict'>":
            return error('Unknown error')
    except:
        return error('Unknown error')

    #print(req)
    req['urls'] = {"facebook": "https://www.facebook.com/anton.naumtsev"}

    req['admin_groups'] = []
    req['user_groups'] = []
    req['invitations'] = []


    params = ['login', 'password', 'first_name', 'last_name', 'email', 'date', 'person_description', 'urls', 'image', 'sex', 'admin_groups', 'user_groups', 'invitations']



    for w in params:
        if w not in req:
            print('Пропущен атрибут ' + w)
            return error('Missing attribute - ' + w)


    account = AccountsDB.get_by_login(req['login'])

    if not account is None:
        print('Логин занят')
        return error('Данный логин уже зарегистрирован')


    account = dict()
    for i in params:
        account[i] = req[i]

    id = AccountsDB.insert(account)


    session['account_id'] = id
    session['login'] = req['login']


    result['status'] = 'Ok'
    result['message'] = ''
    print('Зарегистрировался новый пользователь ' + account['login'])

    return jsonify(result)



@app.route("/req/get_user_info", methods=['GET'])
def req_get_user_info_get():
    result = dict()
    result['status'] = None
    result['message'] = None

    if 'login' not in session:
        return error('User is not authorized')

    account = AccountsDB.get_by_login(session['login'])
    account['date'] = '.'.join(reversed(account['date'].split('-')))
    result['status'] = 'Ok'
    result['message'] = ''
    result['data'] = account

    return jsonify(result)


@app.route("/req/get_user_info/<id>", methods=['GET'])
def req_get_user_info_id_get(id):
    result = dict()
    result['status'] = None
    result['message'] = None

    try:
        id = int(id)
    except:
        return error('Wrong id')


    if 'login' not in session:
        return error('User is not authorized')

    account = AccountsDB.get_by_id(id)

    if account is None:
        return error('Nonexistent id')

    result['status'] = 'Ok'
    result['message'] = ''
    result['data'] = account
    return jsonify(result)


@app.route("/req/get_group_info/<id>", methods=['GET'])
def req_get_group_info_id_get(id):
    result = dict()
    result['status'] = None
    result['message'] = None

    try:
        id = int(id)
    except:
        return error('Wrong id')

    if 'login' not in session:
        return error('User is not authorized')

    group = GroupsDB.get_by_id(id)

    if group is None:
        return error('Nonexistent id')

    group['members_counter'] = len(group['members_id'])

    result['status'] = 'Ok'
    result['message'] = None
    result['data'] = group
    return jsonify(result)


@app.route("/req/get_my_recommendations/<group_id>", methods=['GET'])
def req_get_recomendation_group_id(group_id):
    result = dict()
    result['status'] = None
    result['message'] = None

    try:
        group_id = int(group_id)
    except:
        return error('Wrong group_id')

    if 'login' not in session:
        return error('User is not authorized')

    user = UsersDB.get_one_by_group_id_and_account_id(group_id, session['account_id'])

    if user is None:
        return error('User is not member this group')
    result['status'] = 'Ok'
    result['message'] = ''
    result['data'] = user['result_recommendation']
    return jsonify(result)


@app.route("/req/get_my_posts/<group_id>", methods=['GET'])
def req_get_posts_id(group_id):
    result = dict()
    result['status'] = None
    result['message'] = None

    try:
        group_id = int(group_id)
    except:
        return error('Wrong group_id')

    if 'login' not in session:
        return error('User is not authorized')

    posts = PostsDB.get_all_by_group_id_and_account_id(group_id, session['account_id'])

    result['status'] = 'Ok'
    result['message'] = ''

    result['data'] = posts

    return jsonify(result)



@app.route("/req/update_recommendations/<group_id>/<account_id>", methods=['GET'])
def req_update_recommendations(group_id, account_id):
    result = dict()
    result['status'] = None
    result['message'] = None

    try:
        group_id = int(group_id)
        account_id = int(account_id)
    except:
        return error('Wrong one of ids')

    user = UsersDB.get_one_by_group_id_and_account_id(group_id, account_id)

    all_posts = []

    for id_post in user['posts']:
        post = PostsDB.get_by_id(id_post)
        all_posts.append(post)

    from assessment_functions import update_user_recommendation
    new_user = update_user_recommendation(user, all_posts)

    UsersDB.update_user(new_user)

    result['status'] = 'Ok'
    result['message'] = ''

    return jsonify(result)


@app.route("/req/send_eval/<group_id>", methods=['POST'])
def req_send_eval_group_id(group_id):
    result = dict()
    result['status'] = None
    result['message'] = None

    try:
        group_id = int(group_id)
    except:
        return error('Wrong group_id')

    if 'login' not in session:
        return error('User is not authorized')

    group = GroupsDB.get_by_id(group_id)

    if group is None:
        return error('Nonexistent group_id')



    req = json.loads(request.data)

    req['group_id'] = group_id
    req['author_id'] = session['account_id']

    params = ['appreciated_id', 'group_id', 'date', 'parameters', 'comment']

#
    for par in params:
        if par not in req:
            return error('Missing attribute - ' + par)

    post_id = PostsDB.insert(req)
    user = UsersDB.get_one_by_group_id_and_account_id(group_id, req['appreciated_id'])

    user['posts'].append(post_id)

    UsersDB.update_user(user)

    req_update_recommendations(req['group_id'], req['appreciated_id'])

    result['status'] = 'Ok'
    result['message'] = ''
    return jsonify(result)



@app.route("/req/get_my_groups", methods=['GET'])
def req_get_my_groups_get():
    result = dict()
    result['status'] = None
    result['message'] = None

    if 'login' not in session:
        return error('User is not authorized')


    account = AccountsDB.get_by_id(session['account_id'])


    groups = []
    for group_id in account['user_groups']:
        gr = dict()
        group = GroupsDB.get_by_id(group_id)
        user = UsersDB.get_one_by_group_id_and_account_id(group_id, session['account_id'])

        gr['group_id'] = group_id
        gr['groupname'] = group['groupname']
        gr['groupimage'] = group['groupimage']
        gr['count_members'] = len(group['members_id'])
        gr['count_recommendations'] = len(user['result_recommendation'])
        groups.append(gr)

    result['status'] = 'Ok'
    result['message'] = ''
    result['data'] = groups

    return jsonify(result)


@app.route("/req/create_group", methods=['POST'])
def req_create_group_post():
    result = dict()
    result['status'] = None
    result['message'] = None

    if 'login' not in session:
        return error('User is not authorized')

    req = json.loads(request.data)
    params = ['groupname', 'groupimage']
    gr = dict()
    for par in params:
        if par not in req:
            return error('Missing attribute - ' + par)
        gr[par] = req[par]

    gr['admins_id'] = []
    gr['members_id'] = []

    group_id = GroupsDB.insert(gr)
    add_account_to_group(session['account_id'], group_id)

    group = GroupsDB.get_by_id(group_id)

    user = UsersDB.get_one_by_group_id_and_account_id(group_id, session['account_id'])

    group['admins_id'].append((session['account_id'], user['user_id']))
    GroupsDB.update_group(group)

    account = AccountsDB.get_by_id(session['account_id'])
    account['admin_groups'].append(group_id)

    result['status'] = 'Ok'
    result['message'] = ''
    return jsonify(result)


@app.route("/req/add_user_to_group/<group_id>", methods=['POST'])
def req_add_user_to_group_post(group_id):
    result = dict()
    result['status'] = None
    result['message'] = None

    try:
        group_id = int(group_id)
    except:
        return error('group_id is not integer')


    if 'login' not in session:
        return error('User is not authorized')


    req = json.loads(request.data)
    print(req)
    params = ['login']
    for par in params:
        if par not in req:
            return error('Missing attribute - ' + par)


    flag = False
    group = GroupsDB.get_by_id(group_id)

    for account_id, user_id in group['admins_id']:
        if account_id == session['account_id']:
            flag = True

    if not flag:
        return error('Вы не администратор группы')

    account = AccountsDB.get_by_login(req['login'])
    if account is None:
        return error('Приглашённого пользователя не существует')



    flag = False
    for account_id, user_model in group['members_id']:
        if account['account_id'] == account_id:
            flag = True

    if flag:
        return error('Данный пользователь уже состоит в данной группе')




    add_account_to_group(account['account_id'], group_id)

    result['status'] = 'Ok'
    result['message'] = ''
    return jsonify(result)




@app.route("/req/get_info_about_users_in_group/<group_id>", methods=['GET'])
def req_get_info_about_users_in_group_post(group_id):
    result = dict()
    result['status'] = None
    result['message'] = None

    try:
        group_id = int(group_id)
    except:
        return error('Group_id is not integer')

    if 'login' not in session:
        return error('User is not authorized')


    flag = False
    group = GroupsDB.get_by_id(group_id)

    for account_id, user_id in group['members_id']:
        if account_id == session['account_id']:
            flag = True

    if not flag:
        return error('Вы не являетесь участником данной группы')

    accounts_data = []

    for account_id, user_id in group['members_id']:
        account = AccountsDB.get_by_id(account_id)
        data = dict()
        data['account_id'] = account_id
        data['first_name'] = account['first_name']
        data['last_name'] = account['last_name']
        data['login'] = account['login']
        data['image'] = account['image']
        data['is_admin'] = False

        for acc_id, us_id in group['admins_id']:
            if data['account_id'] == acc_id:
                data['is_admin'] = True

        accounts_data.append(data)

    result['data'] = accounts_data
    result['status'] = 'Ok'
    result['message'] = ''

    return jsonify(result)



@app.route("/group/<group_id>", methods=['GET'])
def req_get_group(group_id):
    if 'login' not in session:
        return redirect('/')

    try:
        group_id = int(group_id)
    except:
        return redirect('/mygroups')


    account = AccountsDB.get_by_id(session['account_id'])
    flag = False
    for gr_id in account['user_groups']:
        if gr_id == group_id:
            flag = True

    if not flag:
        return redirect('/mygroups')

    req_update_recommendations(group_id, session['account_id'])

    return render_template('group_page.html')

#

@app.route("/adminpage", methods=['GET'])
def req_adminpage():
    if 'login' not in session:
        return redirect('/')

    return render_template('admin_page.html')