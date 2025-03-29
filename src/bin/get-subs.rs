use std::{
    env, fs, io,
    path::{Path, PathBuf},
    collections::HashMap,
    // time::SystemTime,
};
use rusqlite::{
    Connection,
    // params,
};
use zip::ZipArchive;
// use chrono::{DateTime, Utc};
use serde_derive::{Serialize, Deserialize};
use regex::Regex;
use lazy_static::lazy_static;

// Configuration
const DEFAULT_LANG: &str = "en";
const DATA_DIR: &str = "~/.config/subtitles";
const CONFIG_PATH: &str = "local-subtitle-providers.json";

// Error type
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

#[derive(Debug, Serialize, Deserialize)]
struct ProviderConfig {
    enabled: Option<bool>,
    db_path: Option<String>,
    id: String,
    zipfiles_table: String,
    zipfiles_num_column: String,
    zipfiles_zipfile_column: String,
    shard_size: Option<u32>,
    db_path_base: Option<String>,
    db_path_format: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Config {
    subtitles_metadata_db_path: String,
    providers: Vec<ProviderConfig>,
}

#[derive(Debug)]
struct Args {
    movie: String,
    lang_list: Vec<String>,
    imdb: Option<String>,
}

fn main() -> Result<()> {
    let args = parse_args()?;
    let config = load_config()?;
    
    let video_filename = Path::new(&args.movie)
        .file_name()
        .ok_or("Invalid movie path")?
        .to_str()
        .ok_or("Invalid UTF-8 in filename")?;
    
    // TODO: Implement guessit functionality in Rust
    let video_parsed = parse_video_filename(video_filename)?;
    
    let metadata_db_path = expand_path(&config.subtitles_metadata_db_path)?;
    let metadata_conn = Connection::open(metadata_db_path)?;
    
    // Process language list
    let lang_list: Vec<String> = args.lang_list.iter()
        .map(|lang| lang4country(lang))
        .map(|lang| lang2letter(&lang))
        .collect();
    
    // Query metadata database
    let (sql_query, sql_args) = build_metadata_query(&video_parsed, &lang_list)?;
    
    let mut stmt = metadata_conn.prepare(&sql_query)?;
    
    /*
    let num_lang_list: Vec<(i64, String)> = stmt.query_map(&sql_args, |row| {
        Ok((row.get(0)?, row.get(1)?))
    })?.collect::<Result<_, _>>()?;
    */

    /*
    let num_lang_list: Vec<(i64, String)> = stmt.query_map(params, |row| {
        Ok((row.get(0)?, row.get(1)?))
    })?.collect::<rusqlite::Result<Vec<_>>>()?;
    */

    // Process providers
    for provider in config.providers {
        if provider.enabled == Some(false) {
            continue;
        }
        
        // Filter subtitles for this provider
        let provider_num_lang_list: Vec<_> = num_lang_list.iter()
            .filter(|(num, _)| {
                let num_range_from = provider.num_range_from().unwrap_or(0);
                let num_range_to = provider.num_range_to().unwrap_or(i64::MAX);
                *num >= num_range_from && *num <= num_range_to
            })
            .collect();
        
        if provider_num_lang_list.is_empty() {
            continue;
        }
        
        let db_path = expand_path(&provider.db_path.ok_or("Missing db_path")?)?;
        let provider_conn = Connection::open(db_path)?;
        
        let num_list: Vec<_> = provider_num_lang_list.iter()
            .map(|(num, _)| num)
            .collect();
        
        let query = format!(
            "SELECT {}, {} FROM {} WHERE {} IN ({})",
            provider.zipfiles_num_column,
            provider.zipfiles_zipfile_column,
            provider.zipfiles_table,
            provider.zipfiles_num_column,
            num_list.iter().map(|_| "?").collect::<Vec<_>>().join(",")
        );
        
        let mut stmt = provider_conn.prepare(&query)?;
        let rows = stmt.query_map(
            rusqlite::params_from_iter(num_list.iter().map(|n| *n)),
            |row| {
                Ok((row.get(0)?, row.get(1)?))
            })?;
        
        for row in rows {
            let (num, zip_content): (i64, Vec<u8>) = row?;
            let lang = provider_num_lang_list.iter()
                .find(|(n, _)| *n == num)
                .map(|(_, l)| lang3letter(l))
                .unwrap_or(DEFAULT_LANG.to_string());
            
            let sub_path = format!("{}.{:08}.{}.srt", 
                Path::new(&args.movie).file_stem().unwrap().to_str().unwrap(),
                num, 
                lang);
            
            let sub_content = extract_sub(&zip_content)?;
            
            fs::write(&sub_path, sub_content)?;
            println!("Wrote subtitle: {}", sub_path);
        }
    }
    
    Ok(())
}

// Helper functions
fn expand_path(path: &str) -> Result<PathBuf> {
    let expanded = if path.starts_with("~/") {
        let home = env::var("HOME")?;
        Path::new(&home).join(&path[2..])
    } else {
        Path::new(path).to_path_buf()
    };
    Ok(expanded)
}

fn parse_args() -> Result<Args> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        return Err("Usage: get-subs <movie-file> [lang]".into());
    }
    
    let lang_list = if args.len() > 2 {
        args[2].split(',').map(String::from).collect()
    } else {
        vec![DEFAULT_LANG.to_string()]
    };
    
    Ok(Args {
        movie: args[1].clone(),
        lang_list,
        imdb: None,
    })
}

fn load_config() -> Result<Config> {
    let config_path = expand_path(CONFIG_PATH)?;
    let config_data = fs::read_to_string(config_path)?;
    Ok(serde_json::from_str(&config_data)?)
}

fn parse_video_filename(filename: &str) -> Result<HashMap<String, String>> {
    // TODO: Implement guessit-like functionality in Rust
    let mut result = HashMap::new();
    // Simple heuristic for now
    if filename.contains("S") && filename.contains("E") {
        result.insert("type".to_string(), "episode".to_string());
    } else {
        result.insert("type".to_string(), "movie".to_string());
    }
    Ok(result)
}

/*
fn build_metadata_query(
    video_parsed: &HashMap<String, String>,
    lang_list: &[String]
) -> Result<(String, Vec<Box<dyn rusqlite::ToSql>>)> {
    let mut query = String::new();
    let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
    
    if video_parsed.get("type") == Some(&"movie".to_string()) {
        query.push_str(
            "SELECT rowid, ISO639 FROM subz_metadata, subz_metadata_fts_MovieName \
             WHERE subz_metadata.rowid = subz_metadata_fts_MovieName.rowid \
             AND subz_metadata_fts_MovieName.MovieName MATCH ? \
             AND subz_metadata.ISO639 IN (");
        
        for (i, lang) in lang_list.iter().enumerate() {
            if i > 0 {
                query.push(',');
            }
            query.push('?');
            params.push(Box::new(lang.clone()));
        }
        
        query.push_str(") AND subz_metadata.SubSumCD = 1 AND subz_metadata.MovieKind = 'movie' LIMIT 500");
        
        // Add title to params
        params.insert(0, Box::new(fts_words("Movie Title"))); // TODO: Get actual title
    } else {
        // Episode query
        unimplemented!("TV episode queries not yet implemented");
    }
    
    Ok((query, params))
}
*/

fn build_and_execute_query(
    conn: &Connection,
    video_parsed: &HashMap<String, String>,
    lang_list: &[String]
) -> Result<Vec<(i64, String)>> {
    let (sql_query, params) = build_metadata_query(video_parsed, lang_list)?;
    let mut stmt = conn.prepare(&sql_query)?;
    
    // Convert parameters to &dyn ToSql references
    let mut query_params: Vec<&dyn rusqlite::ToSql> = Vec::new();
    for param in params {
        query_params.push(&*param);
    }
    
    let results = stmt.query_map(rusqlite::params_from_iter(query_params), |row| {
        Ok((row.get(0)?, row.get(1)?))
    })?;
    
    results.collect::<rusqlite::Result<Vec<_>>>().map_err(Into::into)
}

fn build_metadata_query(
    video_parsed: &HashMap<String, String>,
    lang_list: &[String]
) -> Result<(String, Vec<Box<dyn rusqlite::ToSql>>)> {
    let mut query = String::new();
    let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

/*
// Replace the problematic query execution with proper parameter handling
let mut params: Vec<&dyn rusqlite::ToSql> = Vec::new();

// Add the title parameter
let title_param = fts_words("Movie Title"); // TODO: Get actual title
params.push(&title_param);

// Add language parameters
for lang in &lang_list {
    params.push(lang);
}
*/
    
    if video_parsed.get("type") == Some(&"movie".to_string()) {
        query.push_str(
            "SELECT rowid, ISO639 FROM subz_metadata, subz_metadata_fts_MovieName \
             WHERE subz_metadata.rowid = subz_metadata_fts_MovieName.rowid \
             AND subz_metadata_fts_MovieName.MovieName MATCH ? \
             AND subz_metadata.ISO639 IN (");
        
        query.push_str(&lang_list.iter().map(|_| "?").collect::<Vec<_>>().join(","));
        query.push_str(") AND subz_metadata.SubSumCD = 1 AND subz_metadata.MovieKind = 'movie' LIMIT 500");
        
        // Add title parameter
        params.push(Box::new(fts_words("Movie Title"))); // TODO: Get actual title
        
        // Add language parameters
        for lang in lang_list {
            params.push(Box::new(lang.clone()));
        }
    } else {
        // Episode query
        unimplemented!("TV episode queries not yet implemented");
    }
    
    Ok((query, params))
}

fn extract_sub(zip_content: &[u8]) -> Result<Vec<u8>> {
    let reader = io::Cursor::new(zip_content);
    let mut zip = ZipArchive::new(reader)?;
    
    for i in 0..zip.len() {
        let mut file = zip.by_index(i)?;
        if file.name().ends_with('/') {
            continue;
        }
        
        let mut content = Vec::new();
        io::copy(&mut file, &mut content)?;
        
        // Skip non-subtitle files
        if !file.name().to_lowercase().ends_with(".srt") &&
           !file.name().to_lowercase().ends_with(".sub") {
            continue;
        }
        
        return Ok(content);
    }
    
    Err("No subtitle file found in archive".into())
}

// Language conversion functions
fn lang4country(country: &str) -> String {
    lazy_static! {
        static ref MAP: HashMap<&'static str, &'static str> = {
            let mut m = HashMap::new();
            m.insert("cz", "cs");
            m.insert("jp", "ja");
            // Add more mappings as needed
            m
        };
    }
    MAP.get(country).unwrap_or(&country).to_string()
}

fn lang2letter(lang: &str) -> String {
    // TODO: Implement proper language code conversion
    match lang {
        "ger" => "de".to_string(),
        "eng" => "en".to_string(),
        _ => lang.to_string(),
    }
}

fn lang3letter(lang: &str) -> String {
    // TODO: Implement proper language code conversion
    match lang {
        "de" => "ger".to_string(),
        "en" => "eng".to_string(),
        _ => lang.to_string(),
    }
}

fn fts_words(s: &str) -> String {
    lazy_static! {
        static ref RE: Regex = Regex::new(r"\w+").unwrap();
    }
    RE.find_iter(s)
        .map(|m| m.as_str().to_lowercase())
        .collect::<Vec<_>>()
        .join(" ")
}
