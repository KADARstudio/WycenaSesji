/* Pure tournament functions, shared by the app and the automated tests. */
(function(root){
'use strict';
const clone = value => JSON.parse(JSON.stringify(value));
function shuffle(items, random=Math.random){const a=items.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function filterMovies(movies,options,seen){const services=new Set(options.services);return movies.filter(m=>!seen.includes(m.id)&&m.offers.some(o=>services.has(o.provider))&&(!options.genre||m.genres.some(g=>g.id===options.genre))&&(!options.runtime||(m.runtime>0&&m.runtime<=Number(options.runtime)))&&(!options.rating||(m.rating>0&&m.rating>=Number(options.rating)))&&(!options.year||(m.year>=Number(options.year))));}
function createGame(pool,goal){if(pool.length<2)throw new Error('Do pojedynku potrzebne są co najmniej dwa filmy.');return{deck:pool.map(m=>m.id),cursor:2,pair:[pool[0].id,pool[1].id],champion:null,completed:0,goal:Math.min(goal,pool.length-1),wins:0,done:false};}
function draw(game){if(game.cursor>=game.deck.length)return null;return game.deck[game.cursor++];}
function choose(input,side){if(input.done||![0,1].includes(side))return clone(input);const g=clone(input);const chosen=g.pair[side];if(!chosen)return g;g.completed++;g.wins=chosen===g.champion?g.wins+1:1;g.champion=chosen;const next=draw(g);g.pair[1-side]=next;if(g.completed>=g.goal||!next)g.done=true;return g;}
function replace(input,side){const g=clone(input);const old=g.pair[side];g.pair[side]=draw(g);if(old===g.champion){g.champion=null;g.wins=0;}if(!g.pair[side]){g.champion=g.pair[1-side]||null;g.done=true;}return g;}
function skipBoth(input){const g=clone(input);g.champion=null;g.wins=0;g.pair=[draw(g),draw(g)];if(!g.pair[1]){g.champion=g.pair[0]||null;g.done=true;}return g;}
function continueGame(input,amount=10){const g=clone(input);if(g.pair[0]&&g.pair[1]&&g.cursor<=g.deck.length){g.goal=g.completed+Math.min(amount,g.deck.length-g.cursor+1);g.done=false;}return g;}
const api={clone,shuffle,filterMovies,createGame,choose,replace,skipBoth,continueGame};root.SeansCore=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
