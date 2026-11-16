/* RUSSIAN PARADISE API bridge v0.4
 * Read/auth adapter for the existing FastAPI backend.
 * Never place bot tokens or database credentials in frontend code.
 */
(()=>{'use strict';
const BASE='https://russian-paradise-backend.onrender.com';
let token=sessionStorage.getItem('rp_api_token')||'';
let snapshot={status:'offline',me:null,inventory:null,auctions:null,error:null};
async function request(path,options={}){
  const headers={'Accept':'application/json',...(options.headers||{})};
  if(options.body)headers['Content-Type']='application/json';
  if(token)headers.Authorization='Bearer '+token;
  const response=await fetch(BASE+path,{...options,headers});
  const raw=await response.text();let data=null;try{data=raw?JSON.parse(raw):{}}catch{data={detail:raw}};
  if(!response.ok){const err=new Error(data?.detail||data?.message||('HTTP '+response.status));err.status=response.status;throw err;}
  return data;
}
async function connect(){
  const tg=window.Telegram?.WebApp;
  if(!tg?.initData){snapshot={...snapshot,status:'telegram_required',error:'Telegram initData отсутствует. Открой игру внутри Telegram-бота, чтобы подключить аккаунт. Локальная игра доступна.'};return snapshot;}
  snapshot={...snapshot,status:'connecting',error:null};
  try{
    const auth=await request('/auth/telegram',{method:'POST',body:JSON.stringify({init_data:tg.initData})});
    const newToken=auth.access_token||auth.token||auth.jwt||auth.data?.access_token||auth.data?.token;
    if(!newToken)throw new Error('Сервер ответил без access token. Нужно сверить формат ответа авторизации.');
    token=newToken;sessionStorage.setItem('rp_api_token',token);
    const [me,inventory,auctions]=await Promise.all([
      request('/me'),request('/inventory'),request('/auctions')
    ]);
    snapshot={status:'online',me,inventory,auctions,error:null};
  }catch(error){
    if(error.status){
      snapshot={...snapshot,status:'api_error',error:`Ошибка API (HTTP ${error.status}): ${error.message}`};
    }else if(error instanceof TypeError){
      snapshot={...snapshot,status:'network_error',error:'Сетевая ошибка или блокировка CORS: сервер недоступен из браузера. Локальная игра продолжит работать.'};
    }else{
      snapshot={...snapshot,status:'api_error',error:`Ошибка API: ${error.message||'не удалось обработать ответ сервера'}`};
    }
    if(error.status===401||error.status===403){token='';sessionStorage.removeItem('rp_api_token');}
  }
  return snapshot;
}
function getSnapshot(){return snapshot;}
function hasToken(){return !!token;}
window.RPApi={connect,getSnapshot,hasToken,baseUrl:BASE};
})();
