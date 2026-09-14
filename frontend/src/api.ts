import type {AnalysisResult,DataSource,User} from './types'
const BASE=import.meta.env.VITE_API_URL??'/api/v1'
export const token=()=>localStorage.getItem('asteria_token')
async function request<T>(path:string,options:RequestInit={}):Promise<T>{
 const headers=new Headers(options.headers); if(token())headers.set('Authorization',`Bearer ${token()}`); if(!(options.body instanceof FormData))headers.set('Content-Type','application/json')
 const response=await fetch(`${BASE}${path}`,{...options,headers}); if(!response.ok){const detail=await response.json().catch(()=>({detail:'Request failed'}));throw new Error(detail.detail??'Request failed')} return response.status===204?undefined as T:response.json()
}
export const api={
 login:(email:string,password:string)=>request<{access_token:string;user:User}>('/auth/login',{method:'POST',body:JSON.stringify({email,password})}),
 me:()=>request<User>('/auth/me'), sources:()=>request<DataSource[]>('/data-sources'), source:(id:string)=>request<DataSource>(`/data-sources/${id}`),
 upload:(file:File)=>{const body=new FormData();body.append('file',file);return request<DataSource>('/data-sources/upload',{method:'POST',body})},
 remove:(id:string)=>request<void>(`/data-sources/${id}`,{method:'DELETE'}),
 analyse:(question:string,data_source_id:string,conversation_id?:string)=>request<AnalysisResult>('/analysis/run',{method:'POST',body:JSON.stringify({question,data_source_id,conversation_id})}),
 saved:()=>request<Array<{id:string;title:string;description:string}>>('/saved-analyses'),
 save:(analysis_run_id:string,title:string,chart_config:object)=>request('/saved-analyses',{method:'POST',body:JSON.stringify({analysis_run_id,title,chart_config})}),
 dashboards:()=>request<Array<{id:string;name:string;description:string}>>('/dashboards'),
 createDashboard:(name:string)=>request('/dashboards',{method:'POST',body:JSON.stringify({name})}),
 metrics:()=>request<{query_count:number;failed_query_count:number;average_execution_time_ms:number;data_source_count:number}>('/admin/metrics')
}

