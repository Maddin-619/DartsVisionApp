var os = require('os');
var express = require('express');
var path = require('path');
var favicon = require('serve-favicon');
var logger = require('morgan');
var cookieParser = require('cookie-parser');
var bodyParser = require('body-parser');
var mongoose = require('mongoose');
var amqp = require('amqplib/callback_api');

var routes = require('./routes/index');
var players = require('./routes/players');
var game = require('./routes/game');
var command = require('./routes/command');
var game_logic = require('./game_logic/game_logic');

var app = express();

var spawn = require('child_process').spawn,
    py    = spawn('python', ['DartVision/DartVision.py']);

var hostname = 'martin-desktop';//os.hostname;

mongoose.Promise = global.Promise;

// connect to MongoDB
mongoose.connect('mongodb://' + hostname +'/dartbackend', {
    useMongoClient: true
})
  .then(() =>  console.log('connection to MongoDB succesful'))
  .catch((err) => console.error(err));

// connect to RabbitAMQP Server
amqp.connect('amqp://' + hostname +':5672', function(err, connection) {
    console.log('connection to RabbitAMQP succesful')
    connection.createChannel(function(err, channel) {
        channel.assertQueue('task',{durable: false});
        channel.assertExchange('amq.topic', 'topic', {durable: true});
        channel.assertQueue('points',{durable: false});
        global.channel = channel;
        game_logic();
    });
});


// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

// uncomment after placing your favicon in /public
//app.use(favicon(path.join(__dirname, 'public', 'favicon.ico')));
app.use(logger('dev'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

app.use('/', routes);
app.use('/players', players);
app.use('/game', game);
app.use('/command', command);


// catch 404 and forward to error handler
app.use(function(req, res, next) {
  var err = new Error('Not Found');
  err.status = 404;
  next(err);
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;
