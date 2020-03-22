import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

cors = CORS(app, resources={r"/*": {"origins": "*"}})

# Criar Models

class Rent(db.Model):

  id = db.Column(db.Integer, primary_key=True)
  car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
  client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
  initial_date = db.Column(db.DateTime, default=datetime.utcnow)
  number_of_days = db.Column(db.Integer, default=0)
  finalized = db.Column(db.Integer, default=0)
  park_pass = db.Column(db.Integer, default=0) 

  def __repr__(self):
    return '<Rent {}>'.format(self.id)

class Client(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(200), nullable=False)
  cpf = db.Column(db.Integer, nullable=False)
  rents = db.relationship('Rent', uselist=False, backref='client', lazy=True)
  date_created = db.Column(db.DateTime, default=datetime.utcnow)

  def __repr__(self):
    return '<Client {}>'.format(self.id)

class Car(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  model = db.Column(db.String(200), nullable=False)
  plate = db.Column(db.String(200), nullable=False)
  availability = db.Column(db.Integer, default=1)
  rent = db.relationship('Rent', uselist=False, backref='car')
  date_created = db.Column(db.DateTime, default=datetime.utcnow)

  def __repr__(self):
    return '<Car {}>'.format(self.id)





@app.route('/add_client', methods=['POST'])
def add_client():
  client_data = request.get_json()
  print(client_data)
  client = Client(name=client_data['name'], cpf=client_data['cpf'])
  try:
    db.session.add(client)
    db.session.commit()
    return 'Done'
  except:
    print('Error in adding client to database')

@app.route('/add_car', methods=['POST'])
def add_car():
  car_data = request.get_json()
  print(car_data)
  car = Car(model=car_data['model'], plate=car_data['plate'])
  try:
    db.session.add(car)
    db.session.commit()
    return 'Done'
  except:
    print('Error in adding car to database')

@app.route('/add_rent', methods=['POST'])
def add_rent():
  rent_data = request.get_json()
  print(rent_data)
  car = Car.query.filter_by(plate=rent_data['plate'], availability=1).first()
  client = Client.query.filter_by(cpf=rent_data['cpf']).first()

  rent = Rent(car_id=car.id, client_id=client.id, number_of_days=rent_data['number_of_days'], park_pass=rent_data['park_pass'])
  try:
    db.session.add(rent)
    car.availability = 0
    db.session.commit()
    return 'Done', 201
  except:
    return 'Error in adding rent to database', 400
  
@app.route('/finalize_rent', methods=['POST'])
def finalize_rent():
  rent_data = request.get_json()
  print(rent_data)
  car = Car.query.filter_by(plate=rent_data['plate'], finalized=0).first()
  rent = Rent.query.filter_by(car_id=car.id).first()
  
  try:
    car.availability = 1
    rent.finalized = 1
    db.session.commit()
    return 'Done'
  except:
    print('Error in adding rent to database')

@app.route('/cars', methods=['GET'])
def cars():
  car_list = Car.query.all()
  cars = []
  for car in car_list:
    cars.append({'model': car.model, 'plate': car.plate, 'availability': car.availability})
  
  return jsonify({'cars': cars})

@app.route('/available_cars', methods=['GET'])
def get_available_cars():
  car_list = Car.query.filter_by(availability=1).all()
  cars = []
  for car in car_list:
    cars.append({'model': car.model, 'plate': car.plate})
  return jsonify({'cars': cars})

@app.route('/cars/<string:plate>', methods=['GET'])
def get_car_by_plate(plate):
  try:
    car = Car.query.filter_by(plate=plate).first()
    return {'model': car.model, 'plate': car.plate, 'availability': car.availability}
  except:
    print('Error in getting car in database')
  return 'Error'

@app.route('/available_cars/<string:model>', methods=['GET'])
def get_available_car_by_model(model):
  try:
    car = Car.query.filter_by(model=model, availability=1).first()
    return {'model': car.model, 'plate': car.plate, 'availability': car.availability}
  except:
    print('Error in getting car in database')
  return 'Error'
  
@app.route('/clients', methods=['GET'])
def clients():
  client_list = Client.query.all()
  clients = []
  for client in client_list:
    rent_list = Rent.query.filter_by(client_id=client.id).all()
    rents = []
    for rent in rent_list:
      rents.append({
        'id': rent.id,
        'model': rent.car.model, 
        'plate': rent.car.plate, 
        'initial_date': rent.initial_date, 
        'number_of_days': rent.number_of_days,
        'park_pass': rent.park_pass,
        'finalized': rent.finalized
        })
    clients.append({'name': client.name, 'cpf': client.cpf, 'rents': rents})
  
  return jsonify({'clients': clients})

@app.route('/clients/<int:cpf>', methods=['GET'])
def is_client(cpf):
  try:
    client = Client.query.filter_by(cpf=cpf).first()
    return jsonify({'ok': True, 'name': client.name, 'cpf': client.cpf})
  except:
    return jsonify({'ok': False})

@app.route('/rents', methods=['GET'])
def rents():
  rent_list = Rent.query.all()
  rents = []
  for rent in rent_list:
    rents.append({'id': rent.id, 
      'cpf': rent.client.cpf, 
      'model': rent.car.model, 
      'plate': rent.car.plate,
      'number_of_days': rent.number_of_days,
      'park_pass': rent.park_pass,
      'finalized': rent.finalized
     })
  
  return jsonify({'rents': rents})

@app.route('/delete_car/<string:plate>', methods=['DELETE'])
def delete_car(plate):
  try:
    car = Car.query.filter_by(plate=plate).delete()
    db.session.commit()
  except:
    print('Error in deleting car in database')
  
  return 'Done'

@app.route('/delete_rents', methods=['DELETE'])
def delete_rents():
  try:
    rent_list = Rent.query.all()
    for rent in rent_list:
      rent.car.availability = 1
    db.session.commit()
    db.User.query.delete()
    db.session.commit()
  except:
    print('Error in deleting rents in database')
  
  return 'Done'

@app.route('/time')
def get_current_time():
  return {'time': time.time()}

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80)