var express = require('express');
var router = express.Router();

var mongoose = require('mongoose');
var Game = require('../models/Game.js');
var Player = require('../models/Player.js');

/* GET /game/ */
router.get('/', function(req, res, next) {
  Game
  .find()
  .populate('players')
  .exec(function (err, game) {
    if (err) return next(err);
    if(!game) return res.json(401);
    res.json(game);
  });
});

/* GET /game/players */
router.get('/players', function(req, res, next) {
  Game
  .find()
  .populate('players')
  .exec(function (err, game) {
    if (err) return next(err);
    if(!game[0]) return res.json(401);
    res.json(game[0].players);
  });
});

/* POST /game */
router.post('/', function(req, res, next) {
  Game.create(req.body, function (err, post) {
    if (err) return next(err);
    res.json(post);
  });
});

/* DELETE /game/ */
router.delete('/', function(req, res, next) {
  Game.remove( function (err, post) {
    if (err) return next(err);
    res.json(post);
  });
});

module.exports = router;
