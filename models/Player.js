var mongoose = require('mongoose');
var RoundSchema = new mongoose.Schema({
  value: Number,
  multi: Number
});
var PlayerSchema = new mongoose.Schema({
  name: String,
  totalaverage: { type: Number, default: 0 },
  gameaverage: { type: Number, default: 0 },
  highfinish: { type: Number, default: 0 },
  onehundredandeighty: { type: Number, default: 0 },
  doppelquote: { type: Number, default: 0 },
  wins: { type: Number, default: 0 },
  wonlegs: { type: Number, default: 0 },
  wonsets: { type: Number, default: 0 },
  playedgames: { type: Number, default: 0 },
  points: { type: Number, default: 0 },
  round: [RoundSchema],
  turn: {type: Boolean, default: false},
  updated_at: { type: Date, default: Date.now },
});
module.exports = mongoose.model('Player', PlayerSchema);

