"use strict";

const AthenaExpress = require("athena-express"),
	aws = require("aws-sdk");

	/* AWS Credentials are not required here 
    /* because the IAM Role assumed by this Lambda 
    /* has the necessary permission to execute Athena queries 
    /* and store the result in Amazon S3 bucket */

const athenaExpressConfig = {
	aws,
	db: "meter-data",
	getStats: true
};
const athenaExpress = new AthenaExpress(athenaExpressConfig);

// TODO: Change following to correct error code
const errorCode = 'INT';

exports.handler = async (event, context, callback) => {
	
	let requestBody = {};
	try {
		requestBody = JSON.parse(event.body);
	} catch (e) {
		if (e instanceof TypeError) {
			console.log("---event doesn't have body attribute---");
			console.log(event);
			console.log("--------");
			requestBody = event;
		}
		else if (e instanceof Error) {
			console.log("---event has body attribute in JSON format--")
			console.log(event);
			console.log("--------");
			if (event.body)
				requestBody = event.body;
			else
				requestBody = event;
		}
	} 
	
	console.log(requestBody);
	let startDateTime = requestBody.startDateTime;
    let endDateTime = requestBody.endDateTime;
	
    const sqlQuery = "SELECT d.*, g.col1 as lat, g.col2 as long FROM daily d, geodata g WHERE d.meter_id = g.col0 AND d.reading_type = '" +errorCode+ "' AND d.reading_date_time BETWEEN TIMESTAMP '" +startDateTime+ "' AND TIMESTAMP '" +endDateTime+ "'";
    console.log(sqlQuery);
	//const sqlQuery = "SELECT * FROM daily WHERE reading_type = '11' AND reading_date_time BETWEEN TIMESTAMP '2010-01-03 09:00:01' AND TIMESTAMP '2010-01-03 10:59:59'";

	try {
		let results = await athenaExpress.query(sqlQuery);
		callback(null, results);
	} catch (error) {
		callback(error, null);
	}
};

/*
"body": "{\"startDateTime\": \"2010-01-03 09:00:01\",\"endDateTime\": \"2010-01-03 10:59:59\"}",

"body": {"startDateTime": "2010-01-03 09:00:01","endDateTime": "2010-01-03 10:59:59"},

API Gateway console test
{"startDateTime": "2010-01-03 09:00:01","endDateTime": "2010-01-03 10:59:59"}
*/