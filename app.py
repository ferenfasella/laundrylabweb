from flask import Flask, session, render_template, request, jsonify, redirect, url_for
import requests, os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# app.secret_key = 'your_secret_key'  # Needed to keep the sessions secure
app.secret_key = 'thisissecret'  # Needed to keep the sessions secure



@app.route('/')
def home():
    return 'This is Home!'
#kalo sempet bikin landing page??

@app.route('/test-write')
def test_write():
    try:
        test_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt')
        with open(test_path, 'w') as f:
            f.write('Test write access')
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# @app.route('/utama')
# def utama():
#    return render_template('utama.html')

@app.route('/set_session/<email>')
def set_session(email):
    session['user_email'] = email
    print("Session Data Set:", session)  # Debug output to console
    return jsonify(message=f"Session set for user email: {email}")

@app.route('/get_session')
def get_session():
    print("Current Session Data:", session)  # Debug output to console
    user_email = session.get('user_email', 'Not Logged In')
    return jsonify(user_email=user_email)

@app.route('/delete_session')
def delete_session():
    session.clear()
    print("Session Deleted")  # Debug output to console
    return jsonify(message="Session deleted successfully!")

@app.route('/your-endpoint', methods=['PUT'])
def update_data():
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'No data provided', 'success': False}), 400

    # Process the data here
    # For example, update a database record
    # db.update_record(data)

    return jsonify({'message': 'Data processed successfully', 'success': True})


@app.route('/aatemplate')
def aatemplate():
   return render_template('/admin/aatemplate.html')

@app.route('/tes')
def tes():
   return render_template('/admin/tes.html')






# TOKO
@app.route('/admin/register', methods=['GET', 'POST'])
def adminRegister():
    print("Request methodnya kakak:", request.method)
    if request.method == 'POST':
        print("Request methodnya adik:", request.method)
        admin_email = request.form['email']
        # Here you should add user registration logic
        session['admin_email'] = admin_email  # Set the user email in session
        print("Session set:", session['admin_email'])  # Debug output
        return redirect(url_for('adminBeranda'))
    return render_template('/admin/register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def adminLogin():
    if request.method == 'POST':
        admin_email = request.form['email']
        user_password = request.form['password']  # Assuming you have a password field

        # Authenticate the user via the API
        response = requests.get('https://laundrylab.pocari.id/getAdmin')
        if response.status_code == 200:
            admins = response.json().get('users', [])
            user = next((admin for admin in admins if admin['email'] == admin_email), None)
            if user and user['password'] == user_password:  # Simplified check, consider hashing in production
                # Set user email and admin ID in the session
                session['admin_email'] = admin_email
                session['admin_id'] = user['idAdmin']  # Store admin ID from API
                print("Session set for:", session['admin_email'], "Admin ID:", session['admin_id'])
                return redirect(url_for('adminBeranda'))
            else:
                return 'Login Failed', 401
        else:
            return 'API Error', 500
    else:
        return render_template('/admin/login.html')

@app.route('/admin/beranda', methods=['GET'])
def adminBeranda():
    # Check if admin_email is not in session or is None
    if 'admin_email' not in session or session['admin_email'] is None:
        return redirect(url_for('adminLogin'))  # Redirect to login page if admin_email is not in session or is None
    
    admin_email = session.get('admin_email', 'Not Logged In')
    print("Admin Email:", admin_email)

    petugas_response = requests.get(f'https://laundrylab.pocari.id/getPetugas/{admin_email}')
    if petugas_response.status_code == 200:
        employees = petugas_response.json().get('users', [])
    else:
        employees = []

    categories_response = requests.get(f'https://laundrylab.pocari.id/getKategori/{admin_email}')
    categories = categories_response.json().get('categories', [])

    penilaian_response = requests.get(f'https://laundrylab.pocari.id/getAllPenilaianByLaundry/{admin_email}')
    if penilaian_response.status_code == 200:
        penilaian = penilaian_response.json().get('rates', [])
    else:
        penilaian = []

    return render_template('admin/beranda.html', employees=employees, admin_email=admin_email, categories=categories, penilaian=penilaian   )

@app.route('/admin/profil')
def adminProfil():
    # Check if the user is logged in by checking the session
    if 'admin_email' not in session or session['admin_email'] is None:
        return redirect(url_for('adminLogin'))  # Redirect to login page if not logged in

    admin_email = session['admin_email']
    print("Admin Email:", admin_email)

    # Fetch data from the API
    payment_response = requests.get(f'https://laundrylab.pocari.id/getPembayaran/{admin_email}')
    if payment_response.status_code != 200:
        return "Error fetching payment data", payment_response.status_code
    # print("Response Status Code:", payment_response.status_code)  # Check the response status

    payment_data = payment_response.json()
    users = payment_data.get('users', [])  # Ensure there's a default empty list if 'users' is not found

    # Organize data by payment method
    payment_methods = {
        'bank': [],
        'qris': [],
        'tunai': []
    }

    for method in users:  # Safe access with .get and assuming 'users' contains the payment methods
        if method['paymentMethod'] == 'bank':
            payment_methods['bank'].append(method)
        elif method['paymentMethod'] == 'qris':
            payment_methods['qris'].append(method)
        elif method['paymentMethod'] == 'tunai':
            payment_methods['tunai'].append(method)

    # Fetch operational hours and address from the API
    profile_response = requests.get(f'https://laundrylab.pocari.id/getAdminEmail/{admin_email}')
    if profile_response.status_code != 200:
        return "Error fetching profile data", profile_response.status_code

    profile_data = profile_response.json()
    admin_data = profile_data.get('admin', {})
    days = admin_data.get('days', [])


    # Check if all address fields are available
    address_complete = 'alamat' in admin_data

    laundry_response = requests.get(f'https://laundrylab.pocari.id/getLaundries')
    if laundry_response.status_code == 200:
        laundry_data = laundry_response.json().get('laundries', [])
    else:
        laundry_data = []

    # Pass the organized data, user email, operational hours, and address to the template
    return render_template('admin/profil.html', payment_methods=payment_methods, admin_email=admin_email, users=users, Days=days, 
              address_complete=address_complete , admin_data=admin_data, laundry_data=laundry_data )

@app.route('/admin/pesanan')
def adminPesanan():
    if 'admin_email' not in session or session['admin_email'] is None:
      return redirect(url_for('adminLogin'))  # Redirect to login page if not logged in
   
    # Retrieve the logged-in user's email from the session
    admin_email = session['admin_email']

    pesanan_response = requests.get(f'https://laundrylab.pocari.id/getPesananByEmailLaundry/{admin_email}')
    if pesanan_response.status_code == 200:
        pesanan = pesanan_response.json().get('orders', [])
        # print('ini pesanan', pesanan)
    else:
        pesanan = []

    user_response = requests.get(f'https://laundrylab.pocari.id/getUser')
    if user_response.status_code == 200:
        users = user_response.json().get('users', [])
        user_info = [{'email': user['email'], 'nama': user['nama']} for user in users]
        # print('ini user info', user_info)
    else:
        user_info = []

    admin_response = requests.get('https://laundrylab.pocari.id/getAdmin')
    admin_data = admin_response.json()
    # Initialize a list to store all petugas data
    all_petugas_data = []

    # Loop through each admin and fetch their petugas data
    for admin in admin_data['users']:
        admin_email = admin['email']
        
        # Get petugas email
        petugas_response = requests.get(f'https://laundrylab.pocari.id/getPetugas/{admin_email}')
        petugas_data = petugas_response.json()
        
        # Assuming you want to store all petugas data
        all_petugas_data.extend(petugas_data['users'])

    # petugas = petugas_response.json().get('users', [])
    # petugas_info = [{'email': petugas['email_petugas'], 'nama': petugas['nama_petugas']} for petugas in petugas]
    petugas_info = [{'email': petugas['email_petugas'], 'nama': petugas['nama_petugas']} for petugas in all_petugas_data]
    
    # print('ini petugas info', petugas_info)

    return render_template('/admin/pesanan.html', admin_email=admin_email, pesanan=pesanan, pesanan_response=pesanan_response, user_info=user_info, petugas_info=petugas_info)

@app.route('/admin/detailpesanan')
def adminDetailPesanan():
    if 'admin_email' not in session or session['admin_email'] is None:
      return redirect(url_for('adminLogin'))  # Redirect to login page if not logged in
   
    # Retrieve the logged-in user's email from the session
    admin_email = session['admin_email']

    return render_template('/admin/detailpesanan.html', admin_email=admin_email)

@app.route('/admin/laporan')
def adminLaporan():
    if 'admin_email' not in session or session['admin_email'] is None:
      return redirect(url_for('adminLogin'))  # Redirect to login page if not logged in
   
    # Retrieve the logged-in user's email from the session
    admin_email = session['admin_email']

    return render_template('/admin/laporan.html', admin_email=admin_email)

@app.route('/admin/logout')
def adminLogout():
    session.clear()  # Clear all data from session
    response = redirect(url_for('adminLogin'))  # Redirect to the login page
    response.set_cookie('session', '', expires=0)  # Force the session cookie to expire
    print("Session after clear:", session)  # Debug output to console
    return response






# PETUGAS   
@app.route('/petugas/login', methods=['GET', 'POST'])
def petugasLogin():
    # print('ini method',request.method)
    if request.method == 'POST':
        print('ini request', request)
        # Get admin's email
        admin_response = requests.get('https://laundrylab.pocari.id/getAdmin')
        admin_data = admin_response.json()
        # Initialize a list to store all petugas data
        all_petugas_data = []

        # Loop through each admin and fetch their petugas data
        for admin in admin_data['users']:
            admin_email = admin['email']
            
            # Get petugas email
            petugas_response = requests.get(f'https://laundrylab.pocari.id/getPetugas/{admin_email}')
            petugas_data = petugas_response.json()
            
            # Assuming you want to store all petugas data
            all_petugas_data.extend(petugas_data['users'])

        # Now all_petugas_data contains the petugas data for all admins
        # print(all_petugas_data)

        # Authenticate user
        form_email = request.form.get('email')
        form_password = request.form.get('password')

        # Check if the form email and password match any entry in all_petugas_data
        matched_petugas = next((petugas for petugas in all_petugas_data if petugas['email_petugas'] == form_email and petugas['password_petugas'] == form_password), None)

        if matched_petugas:
            session['petugas_email'] = form_email
            session['petugas_id'] = matched_petugas['id_petugas']
            print('ini session: ', session)
            return redirect(url_for('petugasBeranda'))
        else:
            return 'Login Failed'
    else:
        return render_template('/petugas/login.html')

@app.route('/petugas/logout')
def petugasLogout():
    session.clear()  # Clear all data from session
    response = redirect(url_for('petugasLogin'))  # Redirect to the login page
    response.set_cookie('session', '', expires=0)  # Force the session cookie to expire
    print("Session after clear:", session)  # Debug output to console
    return response

@app.route('/petugas/beranda')
def petugasBeranda():
    if 'petugas_email' not in session or session['petugas_email'] is None:
        return redirect(url_for('petugasLogin'))  # Redirect to login page if not logged in

    # print('inilo beranda session', session)
    petugas_email = session.get('petugas_email', 'Not Logged In')
    print('ini petugas email', petugas_email)

    # # Step 1: Fetch all admin data
    # admin_response = requests.get('https://laundrylab.pocari.id/getAdmin')
    # if admin_response.status_code == 200:
    #     admins = admin_response.json().get('users', [])
    # else:
    #     admins = []
    #     return 'Error fetching admin data', 500

    # # Step 2: Fetch all petugas data for each admin
    # all_petugas_data = []
    # for admin in admins:
    #     admin_email = admin['email']
    #     petugas_response = requests.get(f'https://laundrylab.pocari.id/getPetugas/{admin_email}')
    #     if petugas_response.status_code == 200:
    #         petugas_data = petugas_response.json().get('users', [])
    #         petugas_data_info = [{'email': petugas['email_petugas'], 'emailLaundry': petugas['emailLaundry']} for petugas in petugas_data]
    #         all_petugas_data.extend(petugas_data_info)
    #     else:
    #         return 'Error fetching petugas data', 500
    # # print('ini petugas data', all_petugas_data)

    # # Step 3: Find the adminEmail that corresponds to the petugas_email
    # adminEmail = None
    # for petugas in all_petugas_data:
    #     if petugas['email'] == petugas_email:
    #         adminEmail = petugas['emailLaundry']
    #         # print('ini admin email', adminEmail)
    #         break

    # if not adminEmail:
    #     return 'Admin email not found for the given petugas email', 404
    


    petugas_response = requests.get(f'https://laundrylab.pocari.id/getPetugasByEmail/{petugas_email}')
    if petugas_response.status_code == 200:
        petugas_data = petugas_response.json().get('users', [])
        adminEmail = petugas_data[0].get('emailLaundry', '')
    else:
        petugas_data = []
        return 'Error fetching petugas data', 500
    # # print('ini petugas data', all_petugas_data)







    # Step 4: Use the adminEmail to fetch the kategori
    kategori_response = requests.get(f'https://laundrylab.pocari.id/getKategori/{adminEmail}')
    if kategori_response.status_code == 200:
        kategori = kategori_response.json().get('categories', [])
    else:
        kategori = []
    # print('ini kategori', kategori)

    # Step 5: Use the adminEmail to fetch the pembayaran
    pembayaran_response = requests.get(f'https://laundrylab.pocari.id/getPembayaran/{adminEmail}')
    if pembayaran_response.status_code == 200:
        pembayaran = pembayaran_response.json().get('users', [])
    else:
        pembayaran = []

    pesanan_response = requests.get(f'https://laundrylab.pocari.id/getPesananByEmailPetugas/{petugas_email}')
    if pesanan_response.status_code == 200:
        pesanan = pesanan_response.json().get('orders', [])
        # print('ini pesanan', pesanan)
    else:
        pesanan = []
    
    user_response = requests.get(f'https://laundrylab.pocari.id/getUser')
    if user_response.status_code == 200:
        users = user_response.json().get('users', [])
        user_info = [{'email': user['email'], 'nama': user['nama']} for user in users]
        # print('ini user info', user_info)
    else:
        user_info = []




    return render_template('/petugas/beranda.html', pesanan=pesanan, user_info=user_info, 
                           petugas_email=petugas_email, kategori=kategori, pembayaran=pembayaran)



@app.route('/petugas/detailpesanan')
def petugasDetailPesanan():
    if 'petugas_email' not in session or session['petugas_email'] is None:
        return redirect(url_for('petugasLogin'))  # Redirect to login page if not logged in

    return render_template('/petugas/detailpesanan.html')





# PELANGGAN
# TOKO
@app.route('/pelanggan/register', methods=['GET', 'POST'])
def pelangganRegister():
    if request.method == 'POST':
        user_email = request.form['email']
        user_password = request.form['password']  # Assuming you have a password field
        # user_email = request.form.get('email', '')
        # user_password = request.form.get('password', '')
        print('ini user email: ', user_email)
        print('ini user password: ', user_password)

        # Authenticate the user via the API
        response = requests.get('https://laundrylab.pocari.id/getUser')
        if response.status_code == 200:
            users = response.json().get('users', [])
            user = next((user for user in users if user['email'] == user_email), None)
            print('ini user: ', user)

            if user and user['password'] == user_password:  # Simplified check, consider hashing in production
                # Set user email and admin ID in the session
                session['user_email'] = user_email
                session['user_id'] = user['idUser']  # Store admin ID from API
                print("Session set for:", session['user_email'], "User ID:", session['user_id'])
                return redirect(url_for('pelangganBeranda'))
            else:
                return 'Login Failed', 401
        else:
            return 'API Error', 500
    else:
        return render_template('/pelanggan/register.html')

@app.route('/pelanggan/login', methods=['GET', 'POST'])
def pelangganLogin():
    if request.method == 'POST':
        user_email = request.form['email']
        user_password = request.form['password']  # Assuming you have a password field

        # Authenticate the user via the API
        response = requests.get('https://laundrylab.pocari.id/getUser')
        if response.status_code == 200:
            users = response.json().get('users', [])
            user = next((user for user in users if user['email'] == user_email), None)
            print('ini user: ', user)

            if user and user['password'] == user_password:  # Simplified check, consider hashing in production
                # Set user email and admin ID in the session
                session['user_email'] = user_email
                session['user_id'] = user['idUser']  # Store admin ID from API
                print("Session set for:", session['user_email'], "User ID:", session['user_id'])
                return redirect(url_for('pelangganBeranda'))
            else:
                return 'Login Failed', 401
        else:
            return 'API Error', 500
    else:
        return render_template('/pelanggan/login.html')
    
@app.route('/pelanggan/logout')
def pelangganLogout():
    session.clear()  # Clear all data from session
    response = redirect(url_for('pelangganLogin'))  # Redirect to the login page
    response.set_cookie('session', '', expires=0)  # Force the session cookie to expire
    print("Session after clear:", session)  # Debug output to console
    return response

@app.route('/pelanggan/profil')
def pelangganProfil():
    # Check if the user is logged in by checking the session
    if 'user_email' not in session or session['user_email'] is None:
        return redirect(url_for('pelangganLogin'))  # Redirect to login page if not logged in

    user_email = session['user_email']

    user_response = requests.get(f'https://laundrylab.pocari.id/getUserEmail/{user_email}')
    if user_response.status_code == 200:
        users = user_response.json().get('pelanggan', [])
    else:
        users = []

    rating_response = requests.get(f'https://laundrylab.pocari.id/getAllPenilaian/{user_email}')
    if rating_response.status_code == 200:
        ratings = rating_response.json().get('rates', [])
    else:
        ratings = []

    alamat_response = requests.get(f'https://laundrylab.pocari.id/getAlamat/{user_email}')
    if alamat_response.status_code == 200:
        address = alamat_response.json().get('users', [])
    else:
        address = []
    
    return render_template('pelanggan/profil.html', user_email=user_email, users=users, ratings=ratings, address=address)


@app.route('/pelanggan/beranda', methods=['GET'])
def pelangganBeranda():
    if 'user_email' not in session or session['user_email'] is None:
        return redirect(url_for('pelangganLogin'))  # Redirect to login page if admin_email is not in session or is None
    
    user_email = session.get('user_email', 'Not Logged In')

    alamat_response = requests.get(f'https://laundrylab.pocari.id/getAlamat/{user_email}')
    if alamat_response.status_code == 200:
        address = alamat_response.json().get('users', [])
    else:
        address = []

    laundry_response = requests.get(f'https://laundrylab.pocari.id/getLaundries')
    if laundry_response.status_code == 200:
        laundries = laundry_response.json().get('laundries', [])
    else:
        laundries = []
    
    all_laundry_email = []
    all_laundry_categories = []
    all_global_categories = []
    average_rating_dict = []

    for laundry in laundries:
        laundry_email = laundry.get('email')
        all_laundry_email.append(laundry_email)

        alamat_response = requests.get(f'https://laundrylab.pocari.id/getAdminEmail/{laundry_email}')
        admin_data = alamat_response.json().get('admin', {})

        # Extract the required fields
        alamatLaundry = admin_data.get('alamat', '')
        namaLaundry = admin_data.get('namaLaundry', '')
        bukaTutupLaundry = admin_data.get('bukaTutupLaundry', '')

        # Get categories for each laundry
        categories_response = requests.get(f'https://laundrylab.pocari.id/getKategori/{laundry_email}')
        categories = categories_response.json().get('categories', [])
        # Add alamatLaundry and namaLaundry to each category
        for category in categories:
            category['alamatLaundry'] = alamatLaundry
            category['namaLaundry'] = namaLaundry
            category['bukaTutupLaundry'] = bukaTutupLaundry
        
        all_global_categories.extend(categories)


        penilaian_response = requests.get(f'https://laundrylab.pocari.id/getPenilaian')
        penilaian = penilaian_response.json().get('rates', [])
        penilaianlaundry = [p for p in penilaian if p.get('emailLaundry') == laundry_email]

        # Calculate the average rating
        if penilaianlaundry:
            average_rating = sum(int(p['rate']) for p in penilaianlaundry) / len(penilaianlaundry)
        else:
            average_rating = 0
        
        average_rating_dict.append({
                'emailLaundry': laundry_email,
                'rating': average_rating
            })
    # print('ini laundries', laundries)

    # print("laundry_email", all_laundry_email)
    # print("kategori",all_categories)
    print("kategori global",all_global_categories)
    # print(penilaianlaundry)
    # print(average_rating_dict)
    
    return render_template('pelanggan/beranda.html', address=address, user_email=user_email, 
                           laundries=laundries, all_global_categories=all_global_categories, 
                           average_rating_dict=average_rating_dict)


@app.route('/pelanggan/detaillaundry/<emaillaundry>')
def pelangganDetailLaundry(emaillaundry):
    if 'user_email' not in session or session['user_email'] is None:
        return redirect(url_for('pelangganLogin'))  # Redirect to login page if not logged in

    user_email = session.get('user_email', 'Not Logged In')
    
    alamat_response = requests.get(f'https://laundrylab.pocari.id/getAlamat/{user_email}')
    if alamat_response.status_code == 200:
        address = alamat_response.json().get('users', [])
        # print(address)
    else:
        address = []

    laundry_detail_response = requests.get(f'https://laundrylab.pocari.id/getAdminEmail/{emaillaundry}')
    if laundry_detail_response.status_code == 200:
        laundry_data = laundry_detail_response.json().get('admin', [])
        laundry_data_operasional = laundry_detail_response.json().get('admin', []).get('days', [])
    else:
        laundry_data = []
        laundry_data_operasional = []

    laundry_category_response = requests.get(f'https://laundrylab.pocari.id/getKategori/{emaillaundry}')
    if laundry_category_response.status_code == 200:
        laundry_category = laundry_category_response.json().get('categories', [])
    else:
        laundry_category = []

    penilaian_response = requests.get(f'https://laundrylab.pocari.id/getPenilaian')
    if penilaian_response.status_code == 200:
        penilaian = penilaian_response.json().get('rates', [])
        penilaianlaundry = [p for p in penilaian if p.get('emailLaundry') == emaillaundry]

        # Calculate the average rating
        if penilaianlaundry:
            average_rating = sum(int(p['rate']) for p in penilaianlaundry) / len(penilaianlaundry)
        else:
            average_rating = 0
    else:
        penilaian = []
        penilaianlaundry = []
        average_rating = 0

    return render_template('/pelanggan/detaillaundry.html', laundry_data=laundry_data, 
                laundry_category=laundry_category, laundry_data_operasional=laundry_data_operasional, 
                address=address, penilaianlaundry=penilaianlaundry, average_rating=average_rating)
    
    

@app.route('/pelanggan/pesanan')
def pelangganPesanan():
    if 'user_email' not in session or session['user_email'] is None:
        return redirect(url_for('pelangganLogin'))  # Redirect to login page if not logged in
    
    user_email = session.get('user_email', 'Not Logged In')
    
    pesanan_response = requests.get(f'https://laundrylab.pocari.id/getPesananByEmail/{user_email}')
    if pesanan_response.status_code == 200:
        pesanan = pesanan_response.json().get('orders', [])

        # print('ini pesanan', pesanan)
    else:
        pesanan = []

    admin_response = requests.get(f'https://laundrylab.pocari.id/getAdmin')
    if admin_response.status_code == 200:
        admins = admin_response.json().get('users', [])
        admin_info = [{'email': admin['email'], 'nama': admin['namaLaundry']} for admin in admins]
        # print('ini admin info', admin_info)
    else:
        admin_info = []

    # Initialize a list to store all petugas data
    admin_data = admin_response.json()
    all_petugas_data = []

    # Loop through each admin and fetch their petugas data
    for admin in admin_data['users']:
        admin_email = admin['email']
        
        # Get petugas email
        petugas_response = requests.get(f'https://laundrylab.pocari.id/getPetugas/{admin_email}')
        petugas_data = petugas_response.json()
        
        # Assuming you want to store all petugas data
        all_petugas_data.extend(petugas_data['users'])

    # petugas = petugas_response.json().get('users', [])
    # petugas_info = [{'email': petugas['email_petugas'], 'nama': petugas['nama_petugas']} for petugas in petugas]
    petugas_info = [{'email': petugas['email_petugas'], 'nama': petugas['nama_petugas']} for petugas in all_petugas_data]
    # print('ini petugas info', petugas_info)

    return render_template('/pelanggan/pesanan.html', pesanan=pesanan, admin_info=admin_info, petugas_info=petugas_info)

if __name__ == '__main__':  
    app.run('0.0.0.0',port= 5000,debug=True)