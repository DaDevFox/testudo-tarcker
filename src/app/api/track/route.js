import { HttpStatusCode } from "axios";
import { MongoClient } from "mongodb";

export async function AppendToUserIndex(database, course_id, user_email) {
  const collection = database.collection("dedicated-users");

  if (!course_id || !user_email)
    return new Response(
      "Requires course_id and user_email search parameter with string values"
    );

  var user_record = await collection.findOne({
    email: user_email,
  });

  if (!user_record)
    return new Response(`User ${user_email} could not be located`, {
      status: HttpStatusCode.Unauthorized,
    });

  var updated_watches = user_record.watches;
  if (!updated_watches.includes(course_id)) updated_watches.push(course_id);
  else
    return new Response(
      `User ${user_email} already tracking course ${course_id}`,
      { status: HttpStatusCode.Conflict }
    );

  const result = await collection.updateOne(
    { email: user_email },
    { $set: { watches: updated_watches } },
    { upsert: true }
  );

  if (result.acknowledged) return null;
  else
    return new Response("Result not acknowledged; error?", {
      status: HttpStatusCode.ImATeapot,
    });
}

export async function AppendToFastIndex(database, course_id, user_email) {
  // TODO: thresholds
  // var threshold_min = request.nextUrl.searchParams?.get("threshold_min");
  const collection = database.collection("user-watches");

  if (!course_id || !user_email)
    return new Response(
      "Requires course_id and user_email search parameter with string values"
    );

  var section_watches = await collection.findOne({
    course_id: course_id,
  });

  // user watch row on course doesn't exist; create the record
  if (!section_watches) {
    var section_index_entry = await database
      .collection("section-index")
      .findOne({
        course_id: course_id,
      });

    if (!section_index_entry)
      return new Response(
        `Course section with id ${course_id} could not be located; aborting`,
        { status: HttpStatusCode.NotFound }
      );

    section_watches = {
      course_id: course_id,
      professor: section_index_entry.professor,
      emails: [],
    };
  }

  var updated_emails = section_watches.emails;
  if (!updated_emails.includes(user_email)) updated_emails.push(user_email);
  else
    return new Response(
      `User ${user_email} already tracking course ${course_id}`,
      { status: HttpStatusCode.Conflict }
    );

  const result = await collection.updateOne(
    { course_id: course_id },
    { $set: { emails: updated_emails } },
    { upsert: true }
  );

  if (result.acknowledged) return null;
  else
    return new Response("Result not acknowledged; error?", {
      status: HttpStatusCode.ImATeapot,
    });
}

export async function POST(request) {
  if (!process.env.MONGODB_URI)
    return new Response("", { status: HttpStatusCode.ServiceUnavailable });
  const client = new MongoClient(process.env.MONGODB_URI, {});
  // performs a search with Atlas autocomplete query
  try {
    await client
      .connect()
      .catch((ex) => console.log(`mongodb connect failure ${ex}`));

    // set namespace
    const database = client.db("testudo-index");

    const course_id = request.nextUrl.searchParams?.get("course_id");
    var user_email = request.nextUrl.searchParams?.get("user_email");

    var response = await AppendToFastIndex(database, course_id, user_email);
    if (response) return response;

    response = await AppendToUserIndex(database, course_id, user_email);
    if (response) return response;

    return new Response(`created!`, { status: HttpStatusCode.Created });
  } catch (ex) {
    console.log(ex);
    return new Response(`error: ${ex}`, {
      status: HttpStatusCode.InternalServerError,
    });
  }
}
