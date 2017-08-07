var express = require('express');
var router = express.Router();

var mongoose = require('mongoose');
var Player = require('../models/Player.js');

/* GET /players listing. */
router.get('/', function(req, res, next) {
  Player.find(function (err, players) {
    if (err) return next(err);
    res.json(players);
  });
});

/* GET /players/id */
router.get('/:id', function(req, res, next) {
  Player.findById(req.params.id, function (err, post) {
    if (err) return next(err);
    res.json(post);
  });
});

/* POST /plyers */
router.post('/', function(req, res, next) {
  Player.create(req.body, function (err, post) {
    if (err) return next(err);
    res.json(post);
  });
});

/* PUT /players/:id */
router.put('/:id', function(req, res, next) {
  Player.findByIdAndUpdate(req.params.id, req.body, function (err, post) {
    if (err) return next(err);
    res.json(post);
  });
});

/* DELETE /players/:id */
router.delete('/:id', function(req, res, next) {
  Player.findByIdAndRemove(req.params.id, req.body, function (err, post) {
    if (err) return next(err);
    res.json(post);
  });
});

module.exports = router;
