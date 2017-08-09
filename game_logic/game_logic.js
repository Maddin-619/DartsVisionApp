var express = require('express');
var router = express.Router();

var mongoose = require('mongoose');
var Game = require('../models/Game.js');
var Player = require('../models/Player.js');

var index = 0;
var dart = 0;
var roundInitPoints = 0;
var lock = false;

function nextPlayer(players) {
  lock = false;
  if (index == players.length - 1) {
    index = 0;
  } else {
    index++;
  }
}
function nextDart() {
  if (dart == 2) {
    dart = 0;
  } else {
    dart++;
  }
}

function parseMessage(msg) {
  if (msg.content.toString() == 'next') {
    return 'next';
  } else {
    return {value: parseInt(msg.content.toString().slice(2,msg.content.toString().length)),
            multi: parseInt(msg.content.toString().slice(0,1))
           };
  }
}

module.exports = function() {
    global.channel.consume('points', function(msg) {
    var points = parseMessage(msg);
    console.log("Received %s", points);
      Game
      .find()
      .populate('players')
      .exec(function (err, game) {
        if(!game[0]) {
          global.channel.publish('amq.topic', 'score', new Buffer('No existing game'));
        } else {
          var players = game[0].players;
          var game = game[0];
          if (points == 'next') {
            for(i=0; i < 3; i++) {
              if (!players[index].round[i]) players[index].round[i] = {value: 0, multi: 0};
            }
            players[index].round.splice(0,3);
            players[index].turn = false;
            Player.update({ _id: players[index].id}, players[index], function (err, post) {
              if (err) console.log(err);
            });
            nextPlayer(players);
            players[index].turn = true;
            Player.update({ _id: players[index].id}, players[index], function (err, post) {
              if (err) console.log(err);
            });
            global.channel.publish('amq.topic', 'score', new Buffer(JSON.stringify(players)));
            dart = 0;
          } else if (!lock){
            if(dart == 0) {
              roundInitPoints = players[index].points;
            }
            players[index].round[dart] = {value: points.value, multi: points.multi};

            if (players[index].points == game.gamepoints) {
              if(game.doublein == true) {
                if(players[index].round[dart].multi == 2) {
                  players[index].points -= players[index].round[dart].value;
                }
              } else if (game.doublein == false) {
                players[index].points -= players[index].round[dart].value;
              }
            } else if ((players[index].points - points.value > 1) && (players[index].points - points.value  < game.gamepoints)) {
              players[index].points -= points.value;
            } else if ((players[index].points - points.value) == 0) {
              if (game.doubleout == true) {
                if(points.multi == 2){
                  players[index].points = 0;
                }
              } else if (game.doubleout == false) {
                players[index].points -= points.value;
              }
            } else if (players[index].points - points.value < 0) {
              players[index].points = roundInitPoints;
              lock = true;
            }
            
            if(game.elimination == true) {
              for(i=0; i < players.length; i++) {
                if (index == i) continue;
                if (players[index].points == players[i].points) {
                  players[i].points = game.gamepoints;
                  Player.update({ _id: players[i].id}, players[i], function (err, post) {
                    if (err) console.log(err);
                  });
                }
              }
              
            }
            if(players[index].points == 0) {
              var x = false;
              var timer = setInterval(function(){
                if(!x) {
                  global.channel.sendToQueue('task',new Buffer('light_on'),{persistent: true, deliveryMode: 2});
                } else if(x) {
                  global.channel.sendToQueue('task',new Buffer('light_off'),{persistent: true, deliveryMode: 2});
                }
                x = !x;
              }, 500);
              setTimeout(function(){
                clearInterval(timer);
              },8000);
            }

            nextDart();
            global.channel.publish('amq.topic', 'score', new Buffer(JSON.stringify(players)));
            Player.update({ _id: players[index].id}, players[index], function (err, post) {
              if (err) console.log(err);
            });
          }
        }
      });
    }, {noAck: true});
}
