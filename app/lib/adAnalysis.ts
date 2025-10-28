import { supabase } from "./supabaseClient";

export type AdAnalysisRecord = {
  id: string;
  created_at: string;
  user_id: string;
  title: string | null;
  input: any;
  output: any;
  feature_output?: any;
  brandmeta_output?: any;
  agent_results?: any;
};

export async function fetchUserAnalyses(): Promise<AdAnalysisRecord[]> {
  const { data, error } = await supabase
    .from("ad_analyses")
    .select("id, created_at, user_id, title, input, output, feature_output, brandmeta_output, agent_results")
    .order("created_at", { ascending: false });
  if (error) throw error;
  return data ?? [];
}

export async function createUserAnalysis(params: {
  title: string | null;
  input: any;
  output: any;
  feature_output?: any;
  brandmeta_output?: any;
  agent_results?: any;
}): Promise<AdAnalysisRecord | null> {
  const { data: insertData, error } = await supabase
    .from("ad_analyses")
    .insert({
      title: params.title,
      input: params.input,
      output: params.output,
      feature_output: params.feature_output ?? null,
      brandmeta_output: params.brandmeta_output ?? null,
      agent_results: params.agent_results ?? null,
    })
    .select()
    .single();
  if (error) throw error;
  return insertData ?? null;
}

export async function fetchAnalysisById(id: string): Promise<AdAnalysisRecord | null> {
  const { data, error } = await supabase
    .from("ad_analyses")
    .select("id, created_at, user_id, title, input, output, feature_output, brandmeta_output, agent_results")
    .eq("id", id)
    .single();
  if (error) throw error;
  return data ?? null;
}


