extern crate csv;
extern crate clap;

use std::io;
use std::io::{BufWriter, Write};
use std::io::prelude::*;

use std::fs::File;

use std::cmp::Reverse;
use std::cmp::Ordering;

use csv::{ReaderBuilder};
use clap::{Arg, App};
type Record = (String, String, u64, u64);

// Database available at ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid
fn parse_args() -> clap::ArgMatches<'static>{
	
	App::new("acc2taxid")
		.version("0.1")
		.about("Search for NCBI ID in taxdmp file")
		.author("Cedric Arisdakessian")
		.arg(Arg::with_name("db")
			 .long("db")
			 .takes_value(true)
			 .help("path to taxdmp"))
		.arg(Arg::with_name("query")
			 .long("query")
			 .takes_value(true)
			 .help("path to ncbi ids file"))
		.arg(Arg::with_name("output")
			 .short("o")
			 .help("output file path")
			 .default_value("output.csv"))
		.get_matches()
}

fn main() -> io::Result<()> {

	let args = parse_args();
	let db_path = args.value_of("db").unwrap();
	let query_path = args.value_of("query").unwrap();
	let out_path = args.value_of("output").unwrap();

	let mut db_rdr = ReaderBuilder::new()
        .delimiter(b'\t')
		.has_headers(true)
        .from_path(db_path)
		.expect("Could not find database");

	let mut query_handle = File::open(query_path)?;

	let output_wtr = File::create(out_path).expect("Unable to create file");
	let mut output_wtr = BufWriter::new(output_wtr);

	let mut ids = String::new();
	query_handle.read_to_string(&mut ids).expect("Unable to read data");

	let mut ids: Vec<&str> = ids.trim_end().split('\n').collect();
	(&mut ids).sort_by_key(|&x| Reverse(x));

	let mut cur_query = (&mut ids).pop().unwrap();

	for entry in db_rdr.deserialize() {
		let (acc, _acc_full, taxid, gid): Record = entry?;
		// println!("{} vs {}", cur_query, acc);

		let comparison = &cur_query.cmp(&acc);
		
		if *comparison == Ordering::Greater {
			continue
		}

		if *comparison == Ordering::Equal {
			// println!("{},{},{}", acc, taxid, gid);
			let info = format!("{},{},{}\n", acc, taxid, gid);
			output_wtr.write_all(info.as_bytes()).expect("Unable to write data");
		}

		if *comparison == Ordering::Less {
			eprintln!("{} not found", cur_query);
		}

		cur_query = match (&mut ids).pop() {
			Some(x) => x,
			None => break
		};		
	}

	Ok(())
}
