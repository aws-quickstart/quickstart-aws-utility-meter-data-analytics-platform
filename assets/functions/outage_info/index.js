// MIT No Attribution

// Copyright 2021 Amazon Web Services

// Permission is hereby granted, free of charge, to any person obtaining a copy of this
// software and associated documentation files (the "Software"), to deal in the Software
// without restriction, including without limitation the rights to use, copy, modify,
// merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"use strict"

const AthenaExpress = require("athena-express"),
    aws = require("aws-sdk")

/* AWS Credentials are not required here 
/* because the IAM Role assumed by this Lambda 
/* has the necessary permission to execute Athena queries 
/* and store the result in Amazon S3 bucket */

// outage?error_code={}&start_date_time={}&end_date_time={}
exports.handler = async (event, context, callback) => {

    let dbname = process.env.Db_schema
    let queryParameter = {}

    if (!('queryStringParameters' in event) ||
        !('start_date_time' in event.queryStringParameters) ||
        !('end_date_time' in event.queryStringParameters)
    ) {
        let response = {
            "statusCode": 500,
            "body": "Query parameter couldn't be found in event. One of [error_code, start_date_time, end_date_time] is missing",
            "isBase64Encoded": false
        }

        return callback(null, response)
    }

    queryParameter = event.queryStringParameters

    const athenaExpressConfig = {
        aws,
        db: dbname,
        getStats: true
    }
    const athenaExpress = new AthenaExpress(athenaExpressConfig)

    console.log(queryParameter)
    let errorCode = queryParameter.error_code
    let startDateTime = queryParameter.start_date_time
    let endDateTime = queryParameter.end_date_time

    let sqlQuery = []
    sqlQuery.push(`SELECT d.*, g.col1 as lat, g.col2 as long
                   FROM daily d,
                        geodata g `)
    sqlQuery.push(`WHERE d.meter_id = g.col0 AND d.reading_type = 'ERR' AND d.reading_date_time BETWEEN TIMESTAMP '${startDateTime}' AND TIMESTAMP '${endDateTime}' `)

    if (errorCode) {
        sqlQuery.push(`AND d.error_value = '${errorCode}'`)
    }


    try {
        let queryResults = await athenaExpress.query(sqlQuery.join("").trim())

        let response = {
            "statusCode": 200,
            "body": JSON.stringify(queryResults),
            "isBase64Encoded": false
        }

        callback(null, response)
    } catch (error) {
        callback(error, null)
    }
}
