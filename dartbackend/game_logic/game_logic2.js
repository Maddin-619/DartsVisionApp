var express = require('express');
var router = express.Router();

var mongoose = require('mongoose');
var Game = require('../models/Game.js');
var Player = require('../models/Player.js');

var index = 0;
var dart = 0;

function nextPlayer(players) {
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
          if (points == 'next' || players[index].round.length > 3) {
            var sum = 0;
            for(i=0; i < 3; i++) {
              if (!players[index].round[i]) players[index].round[i] = {value: 0, multi: 0};
              sum += players[index].round[i].value;
            }

            if (players[index].points == game.gamepoints) {
              if(game.doublein == true) {
                var inGame = false;
                for(i=0; i < 3; i++) {
                  if((players[index].round[i].multi == 2) || (inGame)) {
                    players[index].points -= players[index].round[i].value;
                    inGame = true;
                    console.log(players[index].points);
                  }
                }
              } else if (game.doublein == false) {
                players[index].points -= sum;
              }
            } else if ((players[index].points - sum > 1) && (players[index].points - sum  < game.gamepoints)) {
              players[index].points -= sum;
            } else if (players[index].points - sum == 0) {
              if (game.doubleout == true) {
                var temp = players[index].points;
                for(i=0; i < 3; i++) {
                  temp -= players[index].round[i].value;
                  if((players[index].round[i].multi == 2) && (temp == 0)) {
                    players[index].points = 0;
                  }
                }
              } else if (game.doubleout == false) {
                players[index].points -= sum;
              }
            }
            
            if(game.elimination = true) {
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
            players[index].round.splice(0,3);
            global.channel.publish('amq.topic', 'score', new Buffer(JSON.stringify(players)));
            Player.update({ _id: players[index].id}, players[index], function (err, post) {
              if (err) console.log(err);
            });
            nextPlayer(players);
            dart = 0;
          } else {
            players[index].round[dart] = {value: points.value, multi: points.multi};
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
