export type User={id:string;name:string;email:string;role:'analyst'|'admin'}
export type DataSource={id:string;name:string;file_name:string;status:string;row_count:number;column_count:number;created_at:string;profile?:Profile}
export type Profile={row_count:number;column_count:number;duplicate_row_count:number;warnings:string[];inference_notice:string;columns:Array<{name:string;inferred_type:string;missing_count:number;missing_percentage:number;unique_count:number;sample_values:unknown[]}>}
export type AnalysisResult={response_type:string;answer:string;analysis_id?:string;conversation_id:string;data_source_id:string;query:string;columns:string[];rows:Array<Record<string,unknown>>;chart?:{type:string;x?:string;y?:string;title:string};assumptions:string[];warnings:string[];quality?:{confidence:string;row_count:number};execution_time_ms:number;follow_up_suggestions:string[]}

